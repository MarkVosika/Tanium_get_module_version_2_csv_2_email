# Tanium_get_module_version_2_csv_2_email
A python script leveraging the Tanium REST API, to get the installed module version information (module name, last updated date, and installed version) from the https://<tanium_server>/info page and the current available module version information from content.tanium.com.
This information is then combined to a spreadsheet and emailed off to a list of recipients.  The script uses fernet encryption to protect the credentials, separating the key from the ciphertext.

To access the needed information, at a minimum the account used needs a micro admin role with the "Read Server Status" permission. 

This script was originally created to get quick visibility into the status of multiple Tanium installations, without the need to logon to each environment.

Many thanks to the python community for all the online tutorials, whose code has been borrowed/modified to make this possible. 




