# llm_interact

## Before you start

The following instructions assume that your physical hardware is a Raspberry Pi 5 running the Debian GNU/Linux 12 (bookworm) operating system, but the instructions should be easily adaptable to other linux flavours. The main thing is to specify, in the [Dockerfile](Dockerfile) contained in the root directory of this repository, the correct archive (`.tgz`) file for your host architecture from the desired [Ollama release](https://github.com/ollama/ollama/releases).

## Downloading the source code

If you are new to Git / GitHub, you may want to start by reading GitHub's [getting started guide](https://docs.github.com/en/get-started). GitHub is a hosting platform for remote [git](https://git-scm.com/docs) repositories, which is what we are using for version control. To install `git`, run:

    $ sudo apt install git

To get a copy of the current version of the source code using https:

    $ git clone https://github.com/lmcmicu-papers/llm_interact

Using ssh:
    
    $ git clone git@github.com:lmcmicu-papers/llm_interact.git
    
Using GitHub client (if installed):

    $ gh repo clone lmcmicu-papers/llm_interact

## Using interact.py

Note that in order for `interact.py` to run correctly, a directory named `data/` must exist and must include all the same data files as the ones in `default_data`. Unless you only intend to run interact in `direct` mode, you should customize the contents of those files. Run `make test` to verify that *llm_interact* is installed correctly after installing it for the first time. This will create a soft link directing llm_interact to find its data in `default_data`.

To see the command line options for `interact.py`, run:

	$ python3 src/interact.py --help
	usage: interact.py [-h] {conduct-survey,vary,analyze,interact,custom} ...
	
	Interact with LLMs from the Ollama library in various ways
	
	positional arguments:
	  {conduct-survey,vary,analyze,interact,custom}
	                        Use --help with the subcommand name to get help
	                        specific to that command.
	    conduct-survey      Conduct a survey with N participants
	    vary                Generate label variants
	    analyze             Analyze data
	    interact            Directly interact with an LLM
	    custom              Run a customized sequence of interactions with an LLM.
	
	options:
	  -h, --help            show this help message and exit
	
	$ python3 src/interact.py conduct-survey --help
	usage: interact.py conduct-survey [-h] [--participants N] [--mean X]
	                                  [--std-dev X] [--rephrase-ratio R]
	                                  [--participant-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]]
	                                  [--mediator-type {llm,trivial}]
	                                  [--llm-mediator-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]]
	                                  [--llm-mediator-temperature LLM_MEDIATOR_TEMPERATURE]
	                                  [--sleep SECONDS] [--random-seed SEED]
	                                  [--logfile LOGFILE] [--trace]
	                                  OUTPUT
	
	positional arguments:
	  OUTPUT                The filename to which the CSV data will be written
	
	options:
	  -h, --help            show this help message and exit
	  --participants N      The number of participants to survey (default: 100)
	  --mean X              The value of the mean of the normal distribution used
	                        to determine each participant's temperature (default:
	                        0.6).
	  --std-dev X           The value of the standard deviation (or 'width') of
	                        the normal distribution used to determine each
	                        participant's temperature (default: 0.2).
	  --rephrase-ratio R    The proportion of messages (between 0 and 1) that
	                        should be rephrased by the mediator (default: 0.9).
	  --participant-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]
	                        The model LLM to use for every participant (default:
	                        use a random non-trivial model for every participant).
	  --mediator-type {llm,trivial}
	                        The type of mediator to use (default: llm).
	  --llm-mediator-model [{trivial,llama3.1,mistral,pshohel/gemini-3-pro-preview,openchat,gemma3:1b,llama3.2,deepseek-r1,gemma,stable-beluga,orca-mini,samantha-mistral,phi4-mini,zephyr}]
	                        The LLM model to use as a mediator (default: llama3.1,
	                        alternate: mistral). Only applicable to mediators of
	                        type 'llm'
	  --llm-mediator-temperature LLM_MEDIATOR_TEMPERATURE
	                        The temperature of the mediator (default 0.0). Only
	                        applicable to mediators of type 'llm'
	  --sleep SECONDS       The number of seconds to sleep after surveying each
	                        participant (default: 60)
	  --random-seed SEED    Specify a SEED for the random number generator.
	  --logfile LOGFILE     Write logging output to LOGFILE (defaults to
	                        survey.log).
	  --trace               Display stack trace information when exceptions are
	                        caught.
	
	$ python3 src/interact.py vary --help
	usage: interact.py vary [-h] [--models MODEL [MODEL ...]]
	                        [--exclude EXCLUDED_MODEL [EXCLUDED_MODEL ...]]
	                        [--num-variants NUM_VARIANTS] [--sleep SECONDS]
	                        [--random-seed SEED] [--logfile LOGFILE] [--trace]
	                        OUTPUT
	
	positional arguments:
	  OUTPUT                The filename to which the CSV data will be written
	
	options:
	  -h, --help            show this help message and exit
	  --models MODEL [MODEL ...]
	                        A list of the model(s) to use for generating
	                        variations (default: all non-trivial models)
	  --exclude EXCLUDED_MODEL [EXCLUDED_MODEL ...]
	                        A list of models that should not be used when
	                        generating variations. In the case of a conflict
	                        between --models and --exclude, the latter takes
	                        priority. (default: no models excluded)
	  --num-variants NUM_VARIANTS
	                        The total number of variations of the given label to
	                        generate.
	  --sleep SECONDS       The number of seconds to sleep after generating each
	                        set of variations (default: 60 seconds)
	  --random-seed SEED    Specify a SEED for the random number generator
	                        (normally only for testing).
	  --logfile LOGFILE     Write logging output to LOGFILE (defaults to
	                        'vary.log')
	  --trace               Display stack trace information when exceptions are
	                        caught.
	
	$ python3 src/interact.py interact --help
	usage: interact.py interact [-h] [--transient] [--random-seed SEED]
	                            [--logfile LOGFILE] [--trace]
	                            MODEL TEMPERATURE
	
	positional arguments:
	  MODEL               The name of the model to interact with.
	  TEMPERATURE         The temperature to use.
	
	options:
	  -h, --help          show this help message and exit
	  --transient         Do not keep track of the conversation but begin every
	                      question with a clean slate.
	  --random-seed SEED  Specify a SEED for the random number generator (normally
	                      only for testing).
	  --logfile LOGFILE   Write logging output to LOGFILE (defaults to
	                      'interact.log')
	  --trace             Display stack trace information when exceptions are
	                      caught.

## Running Ollama

### Creating a docker container and pulling a model

The recommended way to run Ollama is through `docker`. The [docker documentation](https://docs.docker.com/engine/install/ubuntu/) contains instructions for installing `docker` on Ubuntu, but they should be applicable to most other linux flavours as well.

Once `docker` has been installed, you will then need to perform the following steps to first build a docker image of our virtual ollama server and then create and run an instance of it in a docker container.

1. Build the `llm_interact` image (the '.' at the end of the command tells `docker build` to use the [Dockerfile](Dockerfile) located in the current working directory):

        $ sudo docker build -t "llm_interact" .

2. Verify that the image has been created:

        $ docker images -a
        REPOSITORY        TAG       IMAGE ID       CREATED        SIZE
        llm_interact   latest    33d9326219db   ...            5.82GB

2. Create a new container using the just-created image as a template:

        $ docker create llm_interact

3. Verify that the container has been created:

        $ docker ps -a
        CONTAINER ID   IMAGE             COMMAND          CREATED       STATUS       PORTS     NAMES
        33f27bbf830b   llm_interact   "ollama serve"   ...           Created                nice_northcutt

4. Start the container and verify that the ollama service is running. Note that we can identify the container using either its container id or name (both are randomly generated).

        $ docker start CONTAINER_ID
        $ docker exec CONTAINER_ID ollama -v
        ollama version is 0.12.5

5. (Optional) Pull the desired ollama model (this may take awhile). For instance, to pull the `llama3.1` run:

        $ docker exec CONTAINER_ID ollama pull llama3.1

#### Other useful docker commands

Once the virtual ollama server is started it is normally allowed to run indefinitely until it is either interrupted or the computer is rebooted / shut down. To restart it one then needs to run:

    $ docker start CONTAINER_ID

It is often convenient to start a bash shell within a running container from which one can then execute a series of operations on the container interactively. To do so one uses the command:

    $ docker exec -it CONTAINER_ID bash

To exit the shell, one types `exit`.

For example (note that `hello_world.py` assumes that the `llama3.1` model was pulled -- see above -- and will fail if it was not):

    $ docker exec -it CONTAINER_ID bash
    root@CONTAINER_ID:/# ollama -v
    ollama version is 0.12.5
    root@CONTAINER_ID:/# ls
    bin   dev  hello_world.py  lib	  mnt  proc		 root  sbin  sys  usr
    boot  etc  home		   media  opt  requirements.txt  run   srv   tmp  var
    root@CONTAINER_ID:/# python3 hello_world.py
    Initializing Ollama model llama3.1 ...
    content='Ciao mondo!' additional_kwargs={} response_metadata={'model': 'llama3.1', 'created_at': '2025-10-18T14:40:26.908050049Z', 'done': True, 'done_reason': 'stop', 'total_duration': 13642654501, 'load_duration': 2797468255, 'prompt_eval_count': 35, 'prompt_eval_duration': 9096377017, 'eval_count': 5, 'eval_duration': 1742086158, 'model_name': 'llama3.1', 'model_provider': 'ollama'} id='lc_run--48a37a8b-f125-4940-b79b-ed81a9773727-0' usage_metadata={'input_tokens': 35, 'output_tokens': 5, 'total_tokens': 40}
    Ciao mondo!
    root@CONTAINER_ID:/# exit
    $

Stopping a container:

    $ docker stop CONTAINER_ID

Deleting a container:

    $ docker rm CONTAINER_ID
    
Deleting an image:

    $ docker rmi llm_interact


### Communicating with the Ollama server

#### Using the application programmer interface

We use the [LangChain](https://python.langchain.com/docs/introduction/) library to communicate with the ollama server using python via the script [interact.py](https://github.com/lmcmicu-papers/llm_interact/src/interact.py):

    $ docker exec CONTAINER_ID python3 src/interact.py --help
    usage: interact.py ...

or

    $ docker exec -it CONTAINER_ID bash
    root@CONTAINER_ID:/# python3 src/interact.py --help
    usage: interact.py ...

For further information on the usage of `interact.py`, see the introduction to this document. For the specific API calls that we use, see the [source code](https://github.com/lmcmicu-papers/llm_interact/src/interact.py).


#### Using the `ollama` command

To see the available `ollama` commands, run:

    $ docker exec CONTAINER_ID ollama --help
    Large language model runner

    Usage:
        ollama [flags]
        ollama [command]

    Available Commands:
        serve       Start ollama
        create      Create a model
        show        Show information for a model
        run         Run a model
        stop        Stop a running model
        pull        Pull a model from a registry
        push        Push a model to a registry
        signin      Sign in to ollama.com
        signout     Sign out from ollama.com
        list        List models
        ps          List running models
        cp          Copy a model
        rm          Remove a model
        help        Help about any command

    Flags:
        -h, --help      help for ollama
        -v, --version   Show version information

    Use "ollama [command] --help" for more information about a command.

    
Alternately:

    $ docker exec -it CONTAINER_ID bash
    root@CONTAINER_ID:/# ollama --help
    Large language model runner

    ...
