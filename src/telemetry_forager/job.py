import log as Log
import threading
import time
from wara.wara_manager import WARAManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class WARAEventLoop:
    '''
    listens to an in-memory queue mem_queue for tasks to generate WARA report
    '''

    def event_loop_wara_run_listener(self):
        from main import appconfig, mem_queue # overcome circular import on partially init main.py

        while True:
            try:
                task = mem_queue.dequeue()
                if task:
                    Log.debug('always_running_job receive task wara-report-generation')
                    wap = WARAManager(config=appconfig)
                    wap.run()
                time.sleep(5)
            except Exception as e:
                Log.exception(f'error occured at always_running_job_generate_wara_report: {str(e)}')

    def start(self):
        # run event loop on new thread
        thread = threading.Thread(target=self.event_loop_wara_run_listener)
        thread.start()
        Log.debug('WARA: event loop wara run listener started successfully')



class WARAReportGenScheduledJob:

    # enqueue task to generate wara report
    def enqueue_task_to_generate_wara_report(self):
        from main import mem_queue

        Log.debug('WARA_Report_Generation_Job  enqueue task wara-report-generation')
        mem_queue.enqueue('run_wara')


    # WARA report gen job schedule default to 6 hours
    def init_wara_report_gen_scheduled_job(self):
        scheduler = BackgroundScheduler()
        scheduler.start()
        trigger = CronTrigger(
            year="*", month="*", day="*", hour="*/6", minute="0", second="0"
        )
        scheduler.add_job(
            self.enqueue_task_to_generate_wara_report,
            trigger=trigger,
            name="WARA_Report_Generation_Job",
        )

        Log.debug('WARA_Report_Generation job is setup successfully')



class WARAHistoryCleanUpScheduledJob:

    # enqueue task to generate wara report
    def clean_run_history(self):
        from main import appconfig
        
        Log.debug('WARA: WARA_Clean_Run_History_Job is running')

        wm = WARAManager(appconfig)
        wm.delete_run_history(appconfig.wara_days_to_keep_run_history)

        Log.debug('WARA: WARA_Clean_Run_History_Job is completed')
        

    # WARA report gen job schedule default to 6 hours
    def init_clean_history_scheduled_job(self):
        scheduler = BackgroundScheduler()
        scheduler.start()
        trigger = CronTrigger(
            year="*", month="*", day="*", hour="*", minute="*", second="*/10"
        )
        scheduler.add_job(
            self.clean_run_history,
            trigger=trigger,
            name="WARA_Clean_Run_History_Job",
        )

        Log.debug('WARA: WARA_Clean_Run_History job is setup successfully')
