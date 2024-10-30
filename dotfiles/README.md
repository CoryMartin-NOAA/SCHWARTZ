# Use

The `install_config.py` allows for an easy way to install your schwartz.  Simply modify the config.toml file then run for the machine in question.  Examples are shown below.

## Modify the `config.toml`

The base `config.toml` allows for easy creation for many of NOAA's platforms.  More can be added easily and its a flexible system.

The first section is related to git and GitHub:tm:

```toml
[git]
username = bbakernoaa
email = barry.baker@noaa.gov
hera_key = fake_key_for_hera
gaea_key = fake_key_for_gaea
hopper_key = fake_key_for_hopper
orion_key = fake_key_for_orion
hercules = fake_key_for_hercules
aaqest = fake_key_for_aaqest
byun = fake_key_for_byun
```

Here the fake_key_for_byun is the key generated under your `github -> settings -> Developer Settings -> Personal Access Token`.  The username and email are your GitHub:tm: username and password.

The next section is to handle the email in which you will get reponses.

Then come the machine specific settings including login information and port

## Run the install_config.py

`install_config.py` can be easily run to install your configuration. It is suggested to do a dry run by using the --no-install meeting which will write the files to the current directory instead of the users home directory. Currently the only `shell` supported is `bash`.

```bash
usage: install_config.py [-h] [-f FILENAME] [-m MACHINE] [-s SHELL] [--install | --no-install]

Reads a TOML file and prints its contents.

options:
  -h, --help            show this help message and exit
  -f FILENAME, --filename FILENAME
                        The path to the TOML file
  -m MACHINE, --machine MACHINE
                        The machine in which use the template from
  -s SHELL, --shell SHELL
                        shell on which to install | bash or powershell
  --install, --no-install
                        Install the environment
```

### Example --no-install

```bash
./install_config.py -m hera --no-install
```
