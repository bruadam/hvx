Instruction for the flow: hvx ieq start

1. Ask for the data directory.
2. Validate the data directory and load the data. Only display "Fetching data..." while loading.
3. Ask for which standards, user-defined tests or guidelines to apply, it can be multiple, all or just a few or event none, default is all.
- All means, all combinations between standards, user-defined tests and guidelines and filters and periods. 
4. Process to the analytics and display "Processing analytics..." while processing.
5. Display the analytics interactively, with options to filter by standard, user-defined tests or guidelines, filters and periods, get smart recommendations.
6. Ask if the user wants to generate a report, if yes, generate a PDF report with the analytics and recommendations - Ask if the user wants to use a predefined template or create its own template with choosing which sections to include, charts, tables, recommendations, etc.
-  If using a custom template, ask if the user wants to save the template for future use.
7. Ask if the user wants to save the analytics data to a file, if yes, save to an excel or multiple CSV files for all levels and rooms and metrics. Prefer saving it as JSON but also allow to save the data as a Markdown or TEXT file.
8. End the workflow/exit.


-- 

The workflow should be interactive and user-friendly, guiding the user through each step with clear instructions and options. 

Add informative messages should be displayed at each step to inform the user of the progress and any actions taken but erase the messages once the step is completed to keep the interface clean. Make sure to handle any errors gracefully, providing helpful feedback to the user and allowing them to correct any issues (e.g., invalid directory path, no data found, etc.).
If too serious enable the user to go back to the previous step to correct any mistakes or provide a menu to create a new issue on GitHub with the error details pre-filled. Also add an option to contact support via email with the error details pre-filled. 

If the user wants to exit at any point, provide a confirmation prompt to ensure they want to exit and inform them that any unsaved progress will be lost. 

If the users is not sure about any terminology or questions, provide a help option that explains the terms and provides additional information about the workflow and its steps.