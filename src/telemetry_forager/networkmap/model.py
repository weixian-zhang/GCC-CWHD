
class NetworkMapNode:
    def __init__(self, subscriptionId, resource_group, resource_type, name, category, ip, subnet, vnet, srcPIPLocation):
        self.id = ''
        self.name = ''
        self.category = ''
        self.ip = ''
        self.subnet = ''
        self.vnet = ''
        self.srcPIPLocation = ''
        self.srcRegion = ''
        self.destRegion = ''
        self.azurePublicSrcPIPLocation = ''
        self.azurePublicDestPIPLocation = ''
        self.externalPublicSrcCountry = ''
        self.externalPublicDestCountry = ''
        self.maliciousSrcPIPUrl = '',
        self.maliciousSrcPipThreatType = '',
        self.maliciousSrcPIPThreatDescription = '',
        self.maliciousDestPIPUrl = '',
        self.maliciousDestPIPThreatType = '',
        self.maliciousDestPIPThreatDescription = ''

class NetworkMapEdge:
    def __init__(self, source, target, src_to_dest_data_size, dest_to_srct_data_size, flowType, protocol, connectionType):
        self.source= ''
        self.target = ''
        self.src_to_dest_data_size = ''
        self.dest_to_srct_data_size = ''
        self.flowType = ''
        self.protocol = ''
        self.connectionType = ''

class NetworkMapCategory:
    def __init__(self, name):
        self.name = ''

class NetworkMapResult:
    def __init__(self, nodes, edges, categories):
        self.nodes = nodes
        self.edges = edges
        self.categories = categories

class FilterDataResult:
     def __init__(self, src_subscription,src_rg,src_vnet,src_subnet, src_ip,dest_subscription,dest_rg,dest_vnet,dest_subnet, dest_ip):
        self.src_subscription = src_subscription
        self.src_rg= src_rg
        self.src_vnet= src_vnet
        self.src_subnet= src_subnet
        self.src_ip = src_ip
        self.dest_subscription = dest_subscription
        self.dest_rg = dest_rg
        self.dest_vnet = dest_vnet
        self.dest_subnet = dest_subnet
        self.dest_ip = dest_ip
        
