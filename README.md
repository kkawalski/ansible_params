# Run

> docker build -t ansible_params .

> docker run -d -p "5555:5555" --mount type=bind,src=/home/uladzislau/dev/modest/dynamic_ansible_params/ansible/logs,dst=/app/ansible/logs --mount type=bind,src=/home/uladzislau/dev/modest/dynamic_ansible_params/form_params,dst=/app/form_params ansible_params
