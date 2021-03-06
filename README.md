# Optimal appointment scheduling for Mayo Clinic
An optimal appointment schedule developed for Mayo clinic's chemotherapy outpatient unit

1. Kindly download all files uploaded in the repository to a local folder

2. Kindly populate sample.csv with data (in this case, it contains 22-day outpatient influx data for 7 different types of patients)

3. Kindly populate template.csv with data (in this case, it contains the current appointment scheduling template followed by Mayo Clinic at one of their Chemotherapy Outpatient Units) 

4. Please run chemo current.py , preferrably on Spyder in Anaconda. This will apply 3 pre-defined override policies. Kindly read OverridePolicies.pdf for policy descriptions

5. Line 181, 182 and 183 from chemo current.py outlines the priorities given to policy 1,2 and 3 by defining L3 = 1, L4 = 2, and L5 = 3 respectively, with policy 1 having the most and policy 3 having the least priority. Kindly change the order (from 1 to 3) if you want to redefine prioritites

6. chemo current.py will generate a file named output.xlsx in your local folder, with seperate sheets outlining what the appointment schedule should be for each sample (work day) after applying minimal overrides to accommodate maximum number of patients.

7. chemo current.py will also generate .txt files in your local folder for each sample, with details of the override policies applied to said sample (i.e how many times a policy has been applied and at which time during the day)

8. Kindly populate nurses.xlsx with nurse distribution data for a given work day

9. Please run vln override current.py now to obtain a file titled final current.xlsx. This file will show the number of nurse violations incurred for each sample and also overrides applied.
