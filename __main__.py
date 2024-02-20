import multiprocessing
import subprocess

def run_script(script_path):
    subprocess.run(["python", script_path])

if __name__ == "__main__":

    # Create the database and tables
    subprocess.run(["python", "Python Scripts/createDB.py"])

    # Define the scripts to run in parallel
    scripts_parallel = ['Python Scripts/DEM.py', 'Python Scripts/sentinel.py']

    # Run scripts in parallel
    with multiprocessing.Pool() as pool:
        pool.map(run_script, scripts_parallel)

    # After DEM.py has run, run strata.py and sampling.py in parallel
    scripts_parallel2 = ['Python Scripts/strata.py', 'Python Scripts/sampling.py']

    with multiprocessing.Pool() as pool:
        pool.map(run_script, scripts_parallel2)

    # Run the snow detection script
    subprocess.run(["python", "Python Scripts/snow_detect.py"])