import asyncio
import threading


class PipelineElement:
    def __init__(self, name, timeout=10.0):
        self.name = name
        self.timeout = timeout
        self.next = []
        self.executor = None
        self.task_queue = asyncio.Queue()
        self.shutdown_flag = threading.Event()
        self.loop = asyncio.get_event_loop()
        self.active_tasks: set[asyncio.Task] = set()
        print(f"Initialized {self.name}")

    def add_executor(self, executor):
        self.executor = executor
        self.loop.create_task(self.worker_loop())

    async def process(self, *args):
        raise NotImplementedError

    def save_state(self):
        pass

    def add_next(self, next_element):
        self.next.append(next_element)

    def add_task(self, *args):
        self.task_queue.put_nowait(args)

    async def worker_loop(self):
        while not self.is_shutdown():
            try:
                args = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                task = asyncio.create_task(self.execute_task(*args))
                self.active_tasks.add(task)
                try:
                    await asyncio.wait_for(
                        task, timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    print(
                        f"Task in {self.name} timed out after {self.timeout} seconds, skipping"
                    )
                    task.cancel()
                except Exception as e:
                    print(f"Error executing task in {self.name}: {e}")
                finally:
                    self.active_tasks.discard(task)
                    self.task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in {self.name} worker loop: {e}")

    async def execute_task(self, *args):
        if asyncio.iscoroutinefunction(self.process):
            await self.process(*args)
        else:
            await self.loop.run_in_executor(self.executor, self.process, *args)

    async def propagate_to_next(self, *args):
        for element in self.next:
            element.add_task(*args)

    async def shutdown(self):
        # Process remaining tasks in the queue
        while not self.task_queue.empty():
            try:
                args = self.task_queue.get_nowait()
                await self.process(*args)
            except asyncio.QueueEmpty:
                print(f"Queue is empty in {self.name}")
                break  # Queue is empty, exit the loop
            except Exception as e:
                print(f"Error processing task during shutdown in {self.name}: {e}")
            finally:
                print(f"Task done in {self.name}")
                self.task_queue.task_done()

        # Wait for any active tasks to complete
        if self.active_tasks:
            print(
                f"Waiting for {len(self.active_tasks)} active tasks to complete in {self.name}"
            )
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

        # Save state
        self.save_state()

        self.shutdown_flag.set()
        print(f"Shutdown of {self.name} complete")

    def is_shutdown(self):
        return self.shutdown_flag.is_set()
