##
# @file:  dirwatch.py
# @brief: Class for monitoring the DTN rawdata directory to automatically
#         trigger Globus flow runs. Avoids using the Python watchdog class
#         and its dependence on Linux inotify which works only for local
#         filesystem events.
#

import os
import sys
import time
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
import threading

class DirectoryTrigger:
    """Trigger-handling class which monitors a rawdata directory for the 
    appearance of new run subdirectories and triggers a flow. Intended 
    to monitor data synched to the DTN from an experimental events space.

    Attributes
    ----------
    watch_dir : str
        The top-level directory to watch for the appearence of run dirs.
    delay : int
        Seconds to potentially delay the trigger to start the flow. All files 
        in the input directory must be older than trigger_delay seconds.
    FlowRunner : function
        Callback function to run when an event is observed.

    Methods
    -------
    run
        Run the watcher and handle events.
    flow_thread
        Waits for data to copy in and runs a flow from within a daemon thread.

    """

    def __init__(self, watch_dir, delay, FlowRunner=None):
        """Constructor.

        Parameters
        ----------
        watch_dir : str
            The directory to watch for the appearence of a trigger file.
        delay : int
            Flow run start delay to account for copy-in to DTN. The pipeline 
            input data directory and its contents must have a modification 
            time older than the input delay.
        FlowRunner : function
            Callback function to run when the observer sees an event 
            (default=None).

        """
        self.watch_dir = watch_dir
        self.delay = delay
        self.FlowRunner = FlowRunner

        
    def run(self):
        """Monitor the watchdir and wait for events.

        """        
        logging.root.info("Watcher Started\n")

        if not self.FlowRunner:
            logging.root.info("No callback function defined for events.")
            logging.root.info("Using system print()")
            self.FlowRunner = print

        if not os.path.isdir(self.watch_dir):
            logging.root.error("ERROR: Watch directory does not exist!")
            sys.exit(1)

        logging.root.info(
            f"Monitoring: {self.watch_dir} with delay {self.delay}s\n"
        )

        # What's in the directory to begin with:
        seen = {d for d in os.listdir(self.watch_dir) if d.startswith("run")}
        
        # Look for new directories and start a flow run when a new directory
        # has copied in all its data. Exceptions raised by the flow are
        # handled here, as well as excptions raised by the thread(s):
        try:
            while True:
                current = {
                    d for d in os.listdir(self.watch_dir) if d.startswith("run")
                }
                new = seen ^ current
                logging.root.debug(f"seen {seen} current {current} new {new}")
                {threading.Thread(target=self.flow_thread,
                                  args=(os.path.join(self.watch_dir, n),),
                                  daemon=True).start() for n in new
                 } if new else None
                seen = current
                time.sleep(300)
        except Exception as e:
            logging.root.error(f"ERROR: {e}")
        except:
            logging.root.info("Watcher stopped.")

            
    def flow_thread(self, path):
        """Run a flow from within a daemon thread.
        
        Parameters
        ----------
        path : str
            Path to the directory containing the data files.

        """
        last_mtime = self.get_last_mtime(path)
        logging.root.info(
            f"New run directory: {os.path.abspath(path)} with mtime: "
            f"{last_mtime}, flow will trigger when mtime > {self.delay}..."
        )
        while last_mtime < self.delay:
            logging.root.debug(
                f"last mtime: {last_mtime} < {self.delay}, wait for copy in..."
            )
            time.sleep(5)
            last_mtime = self.get_last_mtime(path)
        logging.root.info(f"Triggered: {os.path.abspath(path)}")
        self.FlowRunner(os.path.abspath(path)) # Runs the flow


    def get_last_mtime(self, path):
        """Get the latest modification time for the directory specified by the 
        path and and all files contained within it.

        Parameters
        ----------
        path : str
            Path to the directory containing data files.

        Returns
        -------
        float
            Last mtime of the path: min of directory mtime and file(s) mtime.

        """
        fmtimes = [
            os.path.getmtime(f) for f in os.scandir(path) if f.is_file()
        ]
        # One of these is the latest mod time:
        fmtime = min([time.time() - t for t in fmtimes]) if fmtimes else 0
        dmtime = time.time() - os.path.getmtime(path)

        return min(dmtime, fmtime)
