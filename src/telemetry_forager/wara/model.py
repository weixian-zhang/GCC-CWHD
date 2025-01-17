from datetime import datetime

class Subscription:
    def __init__(self, id, name):
        self.id = id
        self.name = name
class WARAExecution:
    execution_id: str
    execution_start_time: datetime
    
    def __init__(self, execution_id, execution_start_time,):
        self.execution_id = execution_id if execution_id else ''
        self.execution_start_time = execution_start_time


class WARARecommendation:
    implemented: bool
    number_of_impacted_resources: int
    service_category: str
    resiliency_category: str
    recommendation: str
    impact: str
    best_practice_guidance: str
    read_more: str

    def __init__(self, implemented, number_of_impacted_resources, 
                 service_category, resiliency_category, recommendation, impact, best_practice_guidance, read_more):
        self.implemented = implemented
        self.number_of_impacted_resources = number_of_impacted_resources
        self.service_category = service_category
        self.resiliency_category = resiliency_category
        self.recommendation = recommendation
        self.impact = impact
        self.best_practice_guidance = best_practice_guidance
        self.read_more = read_more


class WARARecommendation:
    def __init__(self, implemented, number_of_impacted_resources, 
                 service_category, resiliency_category, recommendation, impact, best_practice_guidance, read_more):
        self.implemented = implemented
        self.number_of_impacted_resources = number_of_impacted_resources
        self.service_category = service_category
        self.resiliency_category = resiliency_category
        self.recommendation = recommendation
        self.impact = impact
        self.best_practice_guidance = best_practice_guidance
        self.read_more = read_more


class WARAImpactedResource:
    def __init__(self, subscriptionId, resource_group, 
                    Resource_type, name, impact, recommendation, params):
        self.subscriptionId = subscriptionId
        self.resource_group = resource_group
        self.Resource_type = Resource_type
        self.name = name
        self.impact = impact
        self.recommendation = recommendation
        self.params = params


class WARAResourceType:
    def __init__(self, resource_type, number_of_resources):
        self.resource_type = resource_type
        self.number_of_resources = number_of_resources


class WARARetirement:
    def __init__(self, subscriptionId, status, 
                    last_update_time, end_time, impacted_service, title, summary, details, required_action):
        self.subscriptionId = subscriptionId
        self.status = status
        self.last_update_time = last_update_time
        self.end_time = end_time
        self.impacted_service = impacted_service
        self.title = title
        self.summary = summary
        self.details = details
        self.required_action = required_action