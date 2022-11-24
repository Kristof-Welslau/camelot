import logging
import multiprocessing
import os

LOGGER = logging.getLogger(__name__)

class StopProcess(object):
    """Sentinel task to and all tasks to be executed by a process"""
    pass


class ModelProcess(multiprocessing.Process):

    def __init__(self):
        super(ModelProcess, self).__init__()
        self._request_queue = multiprocessing.JoinableQueue()

    def start(self):
        LOGGER.info("Starting model process")
        super(ModelProcess, self).start()

    def run(self):
        LOGGER = logging.getLogger("model_process")
        while True:
            task = self._request_queue.get()
            try:
                if isinstance(task, StopProcess):
                    LOGGER.info("Request to stop process, terminating")
                    break
                else:
                    request, args = task
                    request(*args)
            except Exception as e:
                LOGGER.error('Unhandled exception in model process', exc_info=e)
                import traceback
                traceback.print_exc()
            except:
                LOGGER.error('Unhandled event in model process')
            finally:
                self._request_queue.task_done()
        LOGGER.info("Terminated")

    def post(self, request, exception=None, args = ()):
        assert exception is None
        self._request_queue.put((request, args))

    def _validate_parent(self):
        if not self.is_alive():
            raise Exception('Model is not alive and cannot communicate')
        if self.parent_pid != os.getpid():
            raise Exception('Only the gui can communicate with the model')

    def stop(self):
        """
        Request the worker to finish its ongoing tasks and stop
        """
        self._request_queue.put(StopProcess())
        self.join()
