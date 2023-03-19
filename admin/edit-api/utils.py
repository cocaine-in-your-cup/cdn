from google.cloud import compute
from typing import Dict

def list_regional_managers_ips(
    project_id: str,
) -> Dict[str, str]:
    """
    Returns a dictionary of all the region manager's ips present in a project.

    Args:
        project_id: project ID or project number of the Cloud project you want to use.
    Returns:
        A dictionary with instance names as keys and the ip of the first network interface (usually it's the internal IP) as a string.
    """
    instance_client = compute.InstancesClient()
    request = compute.AggregatedListInstancesRequest()
    request.project = project_id
    # Use the `max_results` parameter to limit the number of results that the API returns per response page.
    request.max_results = 50

    agg_list = instance_client.aggregated_list(request=request)
    managers_ips = {}
    # Fetch the IP of the first network interface of each instance
    for _, response in agg_list:
        if response.instances:
            for instance in response.instances:
                if "regional-manager-" in instance.name:
                    ni = instance.network_interfaces.pop()
                    managers_ips[instance.name] = ni.network_i_p
    return managers_ips

print("i was executed")
