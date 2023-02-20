#!/bin/bash

#####
# Runs an app or script in a container using the DP Kubernetes cluster.
#
# To execute a job using this script, first create a directory and populate
# it with the inputs for the job, as well as the job script to actually run.
# Then execute this script, specifying the full path of the job directory,
# the image name, and the Kubernetes namespace to use:
#
#     ./kubectl_run.sh -d|--jobdir <dir> -i|--image <container image> -n|--namespace <namespace> -- <application> <args> ...
#
# Everything following "--" is the command to execute in the container.
#
# Example:
#
#     ./kubectl_run.sh -d /shared/user/ -i fdulwich/dp3-wsclean -n dp-hippo-[user]-p -- sh my_script.sh
#
#####

set -e

# Parse arguments
JOBDIR=
IMAGE=
NAMESPACE=
while [ $# -gt 0 ]; do
    case $1 in
        -d|--jobdir)
            JOBDIR="$2"
            shift
            ;;
        --jobdir=?*)
            JOBDIR="${1#--jobdir=}"
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift
            ;;
        --namespace=?*)
            NAMESPACE="${1#--namespace=}"
            ;;
        -i|--image)
            IMAGE="$2"
            shift
            ;;
        --image=?*)
            IMAGE="${1#--image=}"
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "[WARNING] Ignoring unknown argument: $1"
    esac
    shift
done

if [ -n "$JOBDIR" ]; then
    echo "[INFO] Using job directory: $JOBDIR"
else
    echo "[ERROR] No job directory specified"
    exit 1
fi

if [ -n "$IMAGE" ]; then
    echo "[INFO] Using container image: $IMAGE"
else
    echo "[ERROR] No container image specified"
    exit 1
fi

if [ -n "$NAMESPACE" ]; then
    echo "[INFO] Using namespace: $NAMESPACE"
else
    echo "[ERROR] No namespace specified"
    exit 1
fi

# From https://stackoverflow.com/a/62087619
function rand-str {
    # Return random alpha-numeric string of given LENGTH
    #
    # Usage: VALUE=$(rand-str $LENGTH)
    #    or: VALUE=$(rand-str)

    local DEFAULT_LENGTH=5
    local LENGTH=${1:-$DEFAULT_LENGTH}

    LC_ALL=C tr -dc a-z0-9 </dev/urandom | head -c $LENGTH
    # LC_ALL=C: required for Mac OS X - https://unix.stackexchange.com/a/363194/403075
    # -dc: delete complementary set == delete all except given set
}

# Generate the job name.
JOBNAME="sdp-test-$(rand-str)"
echo "[INFO] Using job name: $JOBNAME"

echo "[INFO] Creating Kubernetes resources for job"
cat <<END | kubectl create -n $NAMESPACE -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: $JOBNAME
spec:
  backoffLimit: 0
  template:
    spec:
      containers:
        - name: sdp-test
          image: $IMAGE
          imagePullPolicy: Always
          workingDir: $JOBDIR
          volumeMounts:
            - mountPath: /shared
              name: shared
            - mountPath: /private
              name: private
          command:
`for var in "$@"; do echo "            - \"$var\""; done`
          resources:
            limits:
              nvidia.com/gpu: 2
      restartPolicy: Never
      volumes:
        - name: shared
          persistentVolumeClaim:
            claimName: shared
        - name: private
          persistentVolumeClaim:
            claimName: private
END

echo "[INFO] To check the status of the job use \"kubectl get job/$JOBNAME -n $NAMESPACE\""
echo "[INFO] To check if job pod(s) are scheduled use \"kubectl get pod -l job-name=$JOBNAME -n $NAMESPACE\""
echo "[INFO] To view job logs use \"kubectl logs job/$JOBNAME -n $NAMESPACE\""
