.PHONY: all plan apply destroy login

# Use Deploy to deploy the infrastructure
deploy: init apply login

# Use login to login to the cluster

# Use run to run the python script
run: py-init py-run

init:
	cd terraform && terraform init

apply:
	cd terraform && terraform apply

destroy:
	cd terraform && terraform destroy

login:
	aws eks update-kubeconfig --name ebs-test-cluster --region eu-west-1

py-init:
	python3 -m venv venv
	bash -c "source venv/bin/activate && pip3 install -r requirements.txt"

py-run:
	bash -c "source venv/bin/activate && python3 reproduce.py"

py-watch-nodes:
	bash -c "source venv/bin/activate && python3 watch_nodes.py"

py-watch-pods:
	bash -c "source venv/bin/activate && python3 watch_pods.py"
