hvx command-line tool

hvx is a command-line tool for managing and analyzing indoor environmental quality (IEQ) data and energy efficiency. 

It should be structured as follows:

```
hvx

hvx ieq start : Start a new IEQ analysis project interactively.
hvx energy start : Start a new energy efficiency analysis project interactively. -- Not yet implemented
hvx settings : Manage hvx settings.
    hvx settings graphs : Configure graph settings.
    hvx settings templates : Manage report templates.
    hvx settings reports-templates : Manage report templates.

hvx ieq analyze : Analyze IEQ data.
hvx ieq data : Manage IEQ data files.
hvx ieq reports : Generate IEQ reports.
hvx energy analyze : Analyze energy efficiency data. -- Not yet implemented


The rest should be deleted or merged into the ieq start command which is the most important one - going through all the steps interactively - Use central services that are both used for start and data, analyze and reports. To not have duplicate code and logic.