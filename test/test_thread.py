import time

from camelot.test import RunningProcessCase, RunningThreadCase
from camelot.view.model_thread.signal_slot_model_thread import Task, TaskHandler


class ModelThreadCase(RunningThreadCase):

    def test_task( self ):

        def normal_request():
            pass

        task = Task( normal_request )
        task.execute()

        def exception_request():
            raise Exception()

        task = Task( exception_request )
        task.execute()

        def iterator_request():
            raise StopIteration()

        task = Task( iterator_request )
        task.execute()

        def unexpected_request():
            raise SyntaxError()

        task = Task( unexpected_request )
        task.execute()

    def test_handle_tasks(self):
        task_queue = [None, Task( lambda:None )]
        task_handler = TaskHandler(task_queue)
        task_handler.handle_task()
        self.assertFalse(len(task_queue))

    def test_post_task(self):
        self.thread.post(lambda:None)
        time.sleep(1)
        self.assertFalse(len(self.thread._request_queue))

class ModelProcessCase(RunningProcessCase):

    @staticmethod
    def _request():
        pass

    def test_post_task(self):
        self.thread.post(self._request)
        time.sleep(1)
        self.assertFalse(self.thread._request_queue.qsize())
