
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
    def __init__(self, nodes, edges, categories, unique_src_ip, unique_dest_ip):
        self.nodes = nodes
        self.edges = edges
        self.categories = categories
        self.unique_src_ip = unique_src_ip
        self.unique_dest_ip = unique_dest_ip
        
