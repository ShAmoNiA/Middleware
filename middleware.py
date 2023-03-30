import threading
from queue import Queue
from flask import Flask, request

app = Flask(__name__)

# Create a queue to hold incoming requests
request_queue = Queue()

# Define a function to handle each request in a separate thread
def process_request():
    while True:
        # Get the next request from the queue
        request = request_queue.get()

        # Your middleware logic goes here
        # You can modify the request, perform authentication, logging, rate limiting, etc.

        # Forward the modified request to the real server
        response = requests.request(
            method=request.method,
            url=f'https://realserver.com/{request.path}',
            headers=request.headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        # Your middleware logic on the response goes here
        # You can modify the response, add headers, log the response, etc.

        # Return the modified response to the customer
        response_tuple = (
            response.content,
            response.status_code,
            response.headers.items()
        )

        # Put the response back in the queue
        request_queue.task_done()
        request.response_queue.put(response_tuple)

# Create a pool of worker threads to handle requests
for i in range(5):
    t = threading.Thread(target=process_request)
    t.daemon = True
    t.start()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # Create a new request object and add it to the queue
    request_obj = {
        'method': request.method,
        'path': path,
        'headers': request.headers,
        'data': request.get_data(),
        'cookies': request.cookies,
        'response_queue': Queue()
    }
    request_queue.put(request_obj)

    # Wait for the response to be processed by a worker thread
    response_tuple = request_obj['response_queue'].get()

    # Return the modified response to the customer
    return response_tuple

if __name__ == '__main__':
    app.run(debug=True)
