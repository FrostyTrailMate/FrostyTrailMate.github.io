import multiprocessing
import subprocess
import queue

def run_script(script_path, output_queue):
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    output_queue.put(result.stdout)

if __name__ == "__main__":
    # Create the database and tables
    subprocess.run(["python", "Python Scripts/createDB.py"])

    # Define the scripts to run in parallel
    scripts_parallel = ['Python Scripts/DEM.py', 'Python Scripts/sentinel.py']

    # Run scripts in parallel
    output_queue = multiprocessing.Queue()
    processes = []

    for script in scripts_parallel:
        p = multiprocessing.Process(target=run_script, args=(script, output_queue))
        p.start()
        processes.append(p)

    # Wait for all processes to finish
    for p in processes:
        p.join()

    # Print the output messages in the order they were generated
    while not output_queue.empty():
        print(output_queue.get())

    # After DEM.py has run, run strata.py and sampling.py in parallel
    scripts_parallel2 = ['Python Scripts/strata.py', 'Python Scripts/sampling.py']
    processes2 = []

    for script in scripts_parallel2:
        p = multiprocessing.Process(target=run_script, args=(script, output_queue))
        p.start()
        processes2.append(p)

    # Wait for all processes to finish
    for p in processes2:
        p.join()

    # Print the output messages in the order they were generated
    while not output_queue.empty():
        print(output_queue.get())

    # Run the snow detection script
    subprocess.run(["python", "Python Scripts/snow_detect.py"])
