"""
Diagram generated using https://github.com/mingrammer/diagrams tool
Code used to generate the system architecture diagram
"""
from diagrams import Cluster, Diagram
from diagrams.gcp.storage import Storage
from diagrams.gcp.compute import Run
from diagrams.onprem.client import User
from diagrams.aws.database import Redshift

with Diagram("Distributed CDN", show=False):
    
    adminClient = User("Admin Client")

    adminClientAPI = Run("Admin Client API")

    dw = Redshift("analitics")

    with Cluster("Region (e.g., UE,NA,AS)"):
        with Cluster("Regional Manager"):
            manager = Run("")
        with Cluster("Buckets"):
            buckets  = [Storage(""), Storage(""), Storage("")]

        with Cluster("Users EndPoints"):
            userAPIs = [Run("UserAPI"), Run("UserAPI"), Run("UserAPI")]

    adminClient >> adminClientAPI
    adminClientAPI >> dw
    adminClientAPI >> manager
    manager >> buckets
    for bucket, userAPI in zip(buckets, userAPIs):
        bucket >> userAPI
