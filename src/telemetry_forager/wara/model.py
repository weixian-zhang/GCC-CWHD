

class WARAExecution:
    def __init__(self, execution_id, execution_start_time, subscription_ids):
        self.execution_id = execution_id if execution_id else ''
        self.execution_start_time = execution_start_time
        self.subscription_ids = subscription_ids if subscription_ids else []