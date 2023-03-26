from diagrams import Cluster, Diagram
from diagrams.gcp.storage import Storage
from diagrams.gcp.compute import Run
from diagrams.onprem.client import User
from diagrams.aws.database import Redshift

with Diagram("Distributed CDN", show=False):
    
    adminClient = User("Admin Client")

    adminClientAPI = Run("Admin Client API")

    dw = Redshift("Analytics")

    with Cluster("Region (e.g., UE,NA,AS)"):
        with Cluster("Regional Manager"):
            manager = Run("")
        with Cluster("Buckets"):
            buckets  = [Storage(""), Storage(""), Storage("")]
        with Cluster("Proxies Endpoints"):
            proxies = [Run("Proxy"), Run("Proxy"), Run("Proxy")]
        with Cluster("Users Endpoints"):
            userAPIs = [Run("UserAPI"), Run("UserAPI"), Run("UserAPI")]

    adminClient >> adminClientAPI
    adminClientAPI >> dw
    adminClientAPI >> manager
    manager >> buckets
    for bucket, proxy in zip(buckets, proxies):
        bucket >> proxy
    for proxy, userAPI in zip(proxies, userAPIs):
        proxy >> userAPI
