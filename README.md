# EBS-CSI-DRIVER Node Volume Detachment Issue


- Deploy the stack using the following command:

```bash
# Pre: Authenticate with AWS (Default profile or AWS_PROFILE or ENV VARS)
make deploy

# Pre: Authenticate with AWS (Default profile or AWS_PROFILE or ENV VARS)
make login

# Ensure Python3 and Python3-env is installed
make run
```
- You can typically expect the issue to show itself within 60 minutes or faster (the more volumes, the quicker the reproduction).
- You may need to comment out some volumes in `manifests/stateful_set.yml` if you are running the python code against nodes which already have scheduled stateful pods (to prevent getting close to the node volume limit).
- If running on a different cluster, you may need to modify the `manifests/stateful_set.yml` to use a different node selector and tolerations.
- ex. `NODE_SELECTOR="karpenter.sh/provisioner-name=nodes,topology.ebs.csi.aws.com/zone=us-east-1b"`

# Failure Cases

-breakage after 9 attempts
-breakage after 22 attempts


```text
[09:07:22] Deleting pod
[09:07:27] ========== ITERATION 22 ==========
[09:07:27] Waiting for pod to become running on node: ip-10-0-0-47.eu-west-1.compute.internal
[09:07:28] Still waiting for pod to become running after 5 sec. State: Pending. ip-10-0-0-137: 15 | ip-10-0-0-47: 0
[09:07:33] Still waiting for pod to become running after 10 sec. State: Pending. ip-10-0-0-137: 15 | ip-10-0-0-47: 0
[09:07:38] Still waiting for pod to become running after 15 sec. State: Pending. ip-10-0-0-137: 15 | ip-10-0-0-47: 0
[09:07:43] Still waiting for pod to become running after 20 sec. State: Pending. ip-10-0-0-137: 15 | ip-10-0-0-47: 0
[09:07:49] Still waiting for pod to become running after 25 sec. State: Pending. ip-10-0-0-137: 11 | ip-10-0-0-47: 4
[09:07:54] Still waiting for pod to become running after 30 sec. State: Pending. ip-10-0-0-137: 10 | ip-10-0-0-47: 5
[09:07:59] Still waiting for pod to become running after 35 sec. State: Pending. ip-10-0-0-137: 10 | ip-10-0-0-47: 5
[09:08:04] Still waiting for pod to become running after 40 sec. State: Pending. ip-10-0-0-137: 8 | ip-10-0-0-47: 5
[09:08:09] Still waiting for pod to become running after 45 sec. State: Pending. ip-10-0-0-137: 7 | ip-10-0-0-47: 8
[09:08:20] Still waiting for pod to become running after 55 sec. State: Pending. ip-10-0-0-137: 3 | ip-10-0-0-47: 10
[09:08:25] Still waiting for pod to become running after 60 sec. State: Pending. ip-10-0-0-137: 3 | ip-10-0-0-47: 12
[09:08:30] Still waiting for pod to become running after 65 sec. State: Pending. ip-10-0-0-137: 3 | ip-10-0-0-47: 12
[09:08:35] Still waiting for pod to become running after 70 sec. State: Pending. ip-10-0-0-137: 3 | ip-10-0-0-47: 12
...
[09:29:50] Still waiting for pod to become running after 1295 sec. State: Pending. ip-10-0-0-137: 3 | ip-10-0-0-47: 12
```

Looking at the volume attachments, we can see that the volume is attached to the node that is not running the pod:

```text
│ csi-3be1197aede3aed531ce1ca7d9b542384f3a8e00dd86f29ddc7c9ce8ce96049c    ebs.csi.aws.com    pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581    ip-10-0-0-137.eu-west-1.compute.internal     true        13m      │
│ csi-8a0f3949964c083f19479ac991ad6176208ab689a732d5e2921710b56ec833fd    ebs.csi.aws.com    pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00    ip-10-0-0-137.eu-west-1.compute.internal     true        13m      │
│ csi-aca13fbf5392aae1fd5b5df3867f1eefd4632b368a20e4a1d5a6cd6ba106022d    ebs.csi.aws.com    pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74    ip-10-0-0-137.eu-west-1.compute.internal     true        13m      │
```
`csi-3be` has `Creation Timestamp:  2023-06-19T08:06:38Z`, which would've been created on the previous iteration of the pod.
A CSI from a successful migration has `Creation Timestamp:  2023-06-19T08:08:17Z`

Let's look at the logs

```text
I0619 08:07:20.938037      10 event.go:307] "Event occurred" object="default/ebstest" fieldPath="" kind="StatefulSet" apiVersion="apps/v1" type="Normal" reason="SuccessfulCreate" message="create Pod ebstest-0 in StatefulSet ebstest successful"
I0619 08:07:20.942260      10 schedule_one.go:252] "Successfully bound pod to node" pod="default/ebstest-0" node="ip-10-0-0-47.eu-west-1.compute.internal" evaluatedNodes=3 feasibleNodes=1
I0619 08:07:21.042013      10 event.go:307] "Event occurred" object="default/ebstest-0" fieldPath="" kind="Pod" apiVersion="v1" type="Warning" reason="FailedAttachVolume" message="Multi-Attach error for volume \"pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581\" Volume is already exclusively attached to one node and can't be attached to another"
I0619 08:07:21.042050      10 reconciler.go:385] "Multi-Attach error: volume is already exclusively attached and can't be attached to another node" attachedTo=[ip-10-0-0-137.eu-west-1.compute.internal] volume={VolumeToAttach:{MultiAttachErrorReported:false VolumeName:kubernetes.io/csi/ebs.csi.aws.com^vol-09e73bf711ad6e5c3 VolumeSpec:0xc00280a258 NodeName:ip-10-0-0-47.eu-west-1.compute.internal ScheduledPods:[&Pod{ObjectMeta:{ebstest-0 ebstest- default  e4447f40-8a0b-488b-b3c7-bf5cbf63806f 30400 0 2023-06-19 08:07:20 +0000 UTC <nil> <nil> map[app:nginx controller-revision-hash:ebstest-6686649cbc statefulset.kubernetes.io/pod-name:ebstest-0] map[] [{apps/v1 StatefulSet ebstest 57c6c67d-715e-4b70-bda3-a1f95b83088e 0xc000f15607 0xc000f15608}] [] [{kube-controller-manager Update v1 2023-06-19 08:07:20 +0000 UTC FieldsV1 ...
I0619 08:07:21.501207      10 node_authorizer.go:200] "NODE DENY" err="node 'ip-10-0-0-137.eu-west-1.compute.internal' cannot get unknown pv /e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a"
I0619 08:07:21.501853      10 node_authorizer.go:200] "NODE DENY" err="node 'ip-10-0-0-137.eu-west-1.compute.internal' cannot get unknown pv /459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa"
I0619 08:07:21.502179      10 node_authorizer.go:200] "NODE DENY" err="node 'ip-10-0-0-137.eu-west-1.compute.internal' cannot get unknown pv /865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba"
...
I0619 08:07:30.127307      10 reconciler.go:273] "attacherDetacher.DetachVolume started" volume={AttachedVolume:{VolumeName:kubernetes.io/csi/ebs.csi.aws.com^vol-073689cd71c948c7f VolumeSpec:0xc0025c0450 NodeName:ip-10-0-0-137.eu-west-1.compute.internal PluginIsAttachable:true DevicePath: DeviceMountPath: PluginName: SELinuxMountContext:} MountedByNode:false DetachRequestedTime:2023-06-19 08:07:20.940312466 +0000 UTC m=+6213.720318660}

```

It looks like the kubelet is requesting for a PVC that doesn't exist
```json
{
  "kind": "Event",
  "apiVersion": "audit.k8s.io/v1",
  "level": "Request",
  "auditID": "46f27cb4-b1e3-42a1-af08-4937f58e3d8f",
  "stage": "ResponseComplete",
  "requestURI": "/api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba",
  "verb": "get",
  "user": {
    "username": "system:node:ip-10-0-0-137.eu-west-1.compute.internal",
    "uid": "aws-iam-authenticator:<ACCOUNTID>:AROAVR2LRBLM6DTW2ZN4P",
    "groups": [
      "system:bootstrappers",
      "system:nodes",
      "system:authenticated"
    ],
    "extra": {
      "accessKeyId": [
        "ASIAVR2LRBLMWUHBPZIQ"
      ],
      "arn": [
        "arn:aws:sts::<ACCOUNTID>:assumed-role/testcase-eks-node-group-20230619061819078200000009/i-0c6ae60ad1f13fa3d"
      ],
      "canonicalArn": [
        "arn:aws:iam::<ACCOUNTID>:role/testcase-eks-node-group-20230619061819078200000009"
      ],
      "principalId": [
        "AROAVR2LRBLM6DTW2ZN4P"
      ],
      "sessionName": [
        "i-0c6ae60ad1f13fa3d"
      ]
    }
  },
  "sourceIPs": [
    "10.0.0.137"
  ],
  "userAgent": "kubelet/v1.27.1 (linux/amd64) kubernetes/abfec7d",
  "objectRef": {
    "resource": "persistentvolumes",
    "name": "865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba",
    "apiVersion": "v1"
  },
  "responseStatus": {
    "metadata": {},
    "status": "Failure",
    "message": "persistentvolumes \"865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba\" is forbidden: User \"system:node:ip-10-0-0-137.eu-west-1.compute.internal\" cannot get resource \"persistentvolumes\" in API group \"\" at the cluster scope: no relationship found between node 'ip-10-0-0-137.eu-west-1.compute.internal' and this object",
    "reason": "Forbidden",
    "details": {
      "name": "865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba",
      "kind": "persistentvolumes"
    },
    "code": 403
  },
  "requestReceivedTimestamp": "2023-06-19T08:07:21.502039Z",
  "stageTimestamp": "2023-06-19T08:07:21.502238Z",
  "annotations": {
    "authorization.k8s.io/decision": "forbid",
    "authorization.k8s.io/reason": "no relationship found between node 'ip-10-0-0-137.eu-west-1.compute.internal' and this object"
  }
}
```

The first instance of this log is at `2023-06-19T09:07:21.000+01:00`. 

This may indicate that the kubelet is requesting for a PVC that doesn't exist.

```text
**CloudWatch Logs Insights**  
region: eu-west-1  
log-group-names: /aws/eks/ebs-test-cluster/cluster  
start-time: 2023-06-19T08:07:00.000Z  
end-time: 2023-06-19T08:15:00.000Z  
query-string:
filter requestURI like "/api/v1/persistentvolumes/"
| fields @timestamp, requestURI, objectRef.name, user.username
| sort @timestamp asc

---
| @timestamp | requestURI | objectRef.name | user.username |
| --- | --- | --- | --- |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-42d8283d-38c8-49af-a09b-0822b118b40d | pvc-42d8283d-38c8-49af-a09b-0822b118b40d | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-c137720c-af9f-4f89-ba34-cac53e177441 | pvc-c137720c-af9f-4f89-ba34-cac53e177441 | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:14.934 | /api/v1/persistentvolumes/pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-c137720c-af9f-4f89-ba34-cac53e177441 | pvc-c137720c-af9f-4f89-ba34-cac53e177441 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.181 | /api/v1/persistentvolumes/pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.182 | /api/v1/persistentvolumes/pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.182 | /api/v1/persistentvolumes/pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.183 | /api/v1/persistentvolumes/pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.183 | /api/v1/persistentvolumes/pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.183 | /api/v1/persistentvolumes/pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.184 | /api/v1/persistentvolumes/pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.184 | /api/v1/persistentvolumes/pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.184 | /api/v1/persistentvolumes/pvc-42d8283d-38c8-49af-a09b-0822b118b40d | pvc-42d8283d-38c8-49af-a09b-0822b118b40d | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.680 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.680 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:21.680 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:22.183 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:22.183 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:22.184 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:23.186 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:23.186 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:23.436 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:25.197 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:25.197 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:25.439 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:29.197 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:29.197 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:29.448 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:37.464 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:37.464 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:37.464 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:53.277 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:53.277 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:07:53.528 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:08:25.391 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:08:25.391 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:08:25.641 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:09:29.588 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:09:29.588 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:09:29.838 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.602 | /api/v1/persistentvolumes/pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.602 | /api/v1/persistentvolumes/pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.602 | /api/v1/persistentvolumes/pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-c137720c-af9f-4f89-ba34-cac53e177441 | pvc-c137720c-af9f-4f89-ba34-cac53e177441 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.603 | /api/v1/persistentvolumes/pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.604 | /api/v1/persistentvolumes/pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.604 | /api/v1/persistentvolumes/pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.604 | /api/v1/persistentvolumes/pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:09:35.853 | /api/v1/persistentvolumes/pvc-42d8283d-38c8-49af-a09b-0822b118b40d | pvc-42d8283d-38c8-49af-a09b-0822b118b40d | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:31.639 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:11:31.639 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:11:31.889 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-c137720c-af9f-4f89-ba34-cac53e177441 | pvc-c137720c-af9f-4f89-ba34-cac53e177441 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.679 | /api/v1/persistentvolumes/pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.680 | /api/v1/persistentvolumes/pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.680 | /api/v1/persistentvolumes/pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.680 | /api/v1/persistentvolumes/pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.680 | /api/v1/persistentvolumes/pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.680 | /api/v1/persistentvolumes/pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:49.680 | /api/v1/persistentvolumes/pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:11:50.180 | /api/v1/persistentvolumes/pvc-42d8283d-38c8-49af-a09b-0822b118b40d | pvc-42d8283d-38c8-49af-a09b-0822b118b40d | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:13:33.706 | /api/v1/persistentvolumes/e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | e706dce472d961b5b5ad8c80796434bb34d486f1ec17127a20f92b2084f4e61a | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:13:33.706 | /api/v1/persistentvolumes/865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | 865eec5824122cafa9f6e444e622fe30a1c13e570db92581035f7f88a62c02ba | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:13:34.207 | /api/v1/persistentvolumes/459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | 459dd0b57d9c28d03b71f9173d434cdac9ddf3143adfa0427d76e1c8c585cdaa | system:node:ip-10-0-0-137.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.551 | /api/v1/persistentvolumes/pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | pvc-c9e2df00-8816-4eb3-a6f9-9625e863a883 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.551 | /api/v1/persistentvolumes/pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | pvc-37f717b4-e9de-4a20-82b8-78c924f72e70 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.551 | /api/v1/persistentvolumes/pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | pvc-f68ec211-c493-49ae-9759-f9e8785cc81f | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.551 | /api/v1/persistentvolumes/pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | pvc-b5a003b5-59b1-4e4f-a5e9-ea9a9fba5f74 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.551 | /api/v1/persistentvolumes/pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | pvc-a0f4e7ea-bb72-4a03-b27f-a4e622e39636 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.551 | /api/v1/persistentvolumes/pvc-c137720c-af9f-4f89-ba34-cac53e177441 | pvc-c137720c-af9f-4f89-ba34-cac53e177441 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | pvc-9de02be3-4ef4-45de-83e4-691b1e9aa60a | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | pvc-e3a0aa4e-b01f-49f2-a03c-ddf72ad07581 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | pvc-7344ee8e-44b6-479f-b1c9-89b3883c1fd7 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | pvc-84960c94-000a-40a2-b41b-3b65b3c2f334 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | pvc-6e9bd0ab-1f1f-4a57-bf6f-12d2ca7f3d52 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | pvc-e481ed4a-6ea2-4e25-b0a9-9dd618cdd152 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.801 | /api/v1/persistentvolumes/pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | pvc-0353f88e-d60a-4482-9c6f-5e71668a1f94 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.802 | /api/v1/persistentvolumes/pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | pvc-8cc2af0d-3e94-4f0e-976c-585c2f94cd00 | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
| 2023-06-19 08:14:07.802 | /api/v1/persistentvolumes/pvc-42d8283d-38c8-49af-a09b-0822b118b40d | pvc-42d8283d-38c8-49af-a09b-0822b118b40d | system:node:ip-10-0-0-47.eu-west-1.compute.internal |
---
```

This is undesired behaviour, which has been patched in upstream by https://github.com/kubernetes/kubernetes/pull/116138