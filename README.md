# Run

> docker build -t ansible_params .

> docker run -d -p "5555:5555" --mount type=bind,src=${pwd}/ansible/logs,dst=/app/ansible/logs ansible_params
