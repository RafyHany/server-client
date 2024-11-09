import requests
import threading
import time
import matplotlib.pyplot as plt

url = 'http://localhost:8080/files/profile.jpg'


def make_request():
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    response_time = end_time - start_time
    print(f'Response time: {response_time:.2f} seconds')
    return response_time


def test_performance(num_clients):
    response_times = []

    threads = []
    for _ in range(num_clients):
        thread = threading.Thread(target=lambda: response_times.append(make_request()))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return response_times


def evaluate_performance():
    clients = [1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    avg_response_times = []

    for client_count in clients:
        print(f'Testing with {client_count} clients...')
        response_times = test_performance(client_count)
        avg_response_time = sum(response_times) / len(response_times)
        avg_response_times.append(avg_response_time)

    plt.figure(figsize=(10, 6))
    plt.plot(clients, avg_response_times, marker='o', linestyle='-', color='#1f77b4', markersize=8,
             label='Avg Response Time')
    plt.title('Server Performance: Response Time vs. Number of Clients', fontsize=16, fontweight='bold',
              color='#003366')
    plt.xlabel('Number of Clients', fontsize=12, color='#003366')
    plt.ylabel('Average Response Time (seconds)', fontsize=12, color='#003366')
    plt.grid(True, linestyle='--', color='#e1eaff', alpha=0.7)
    plt.gca().set_facecolor('white')
    plt.xticks(clients, fontsize=10, color='#003366')
    plt.yticks(fontsize=10, color='#003366')
    plt.legend(facecolor='white', edgecolor='#1f77b4', fontsize=12)
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    evaluate_performance()
