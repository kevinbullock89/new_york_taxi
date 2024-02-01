# Taxi Data Analysis Project

Author: Kevin Bullock

## Set-up Azure Cloud Infrastructure

This project shows how Apache Airflow installed in a Docker container on an Azure VM can be used to load taxi data into with a data pipeline. The data in parquet files is loaded from Airflow into a mysql server and from there the data is loaded into a Power BI dataset.

### Airflow and Docker in Azure VM

1. **Azure VM:**
    - Creation of a VM in the [Azure portal](https://portal.azure.com/#home)
    - Specify which name and in which resource group the VM is to be created
    - Open SSH ports
    - Size: Standard B4ms (4 vcpus, 16 GiB memory), with a smaller VM, there may be problems with the execution of Airflow

2. **Docker Installation:**
   - Install Docker on the Azure VM.
   - Download link: [Docker Installation](https://docs.docker.com/engine/install/ubuntu/)
   - To solve Docker permission problems: [Stack Overflow](https://stackoverflow.com/questions/48957195/how-to-fix-docker-got-permission-denied-issue)

3. **Airflow Installation:**
   - Install Airflow using Docker Compose by following the instructions [Airflow with Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
   - Configure necessary environment variables and settings.
   - Deactivating the examples in the docker-compose file and allowed the connection to be tested:

    ```sh
        AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
        AIRFLOW__CORE__TEST_CONNECTION: Enabled # In Airflow 2.7+ testing connections by any of the methods above is disabled by default [Astronomer Docs](https://docs.astronomer.io/learn/connections)
    ```
    - Create a Volume Mount for the taxi data files

    ```sh
        volumes:
            - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
            - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
            - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
            - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
            - /home/azureuser-airflow/taxi_data:/data   # New line for taxi data
    ```

4. **Azure MySQL Database:**
   - Create an Azure MySQL database to store the taxi data
   - Ensure the necessary credentials and connection details are set
   - Created User and Password
   - Open the ports of the firewall so that Airflow can access them
   - Create Connection in Airflow mysql_airflow 

5. **VS Code:**
    - Accessing the Azure VM with VS Code via SSH
    - Installation of Visual Studio Code Server [VS Code Server](https://code.visualstudio.com/docs/remote/vscode-server)
    - With port forwarding I could access the Airflow interface with it

6. **Installing Python packages:**
    - The following Python packages must be installed:

    ```sh
        sudo apt-get install pkg-config
        pip install mysqlclient
        pip install apache-airflow-providers-mysql
        pip install pandas pyarrow
        pip install pandas 
    ```

7. **DBeaver:**
    - To connect to the database I used DBeaver
    - Create Database
    - Set the MySQL server parameter require_secure_transport to OFF to be able to access the server

8. **Power BI:**
    - Download Power BI Desktop [PBI download](https://powerbi.microsoft.com/en-us/downloads/)
    - Download MySQL Connector [Connector](https://dev.mysql.com/downloads/connector/net/)
    - load the data from MySQL with the SQL-User and password

## Data Pipeline

### Loading Taxi Data into MySQL Database

The data pipeline is designed to load taxi data into the Azure MySQL database. The parquet files were downloaded from the website [NYC Taxi Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) and manually loaded onto the VM. 

Below is an overview of the code and its functionality:

#### Airflow DAG (Directed Acyclic Graph) ####

In this Airflow DAG TLC_Trip_Record the parquet files are loaded into a mysql table:

- load_data_to_mysql() function creates a connection to mysql and then loads it into the specified table. MySqlHook uses the connection already created in Airflow.
- taxi_data_from_parquet() function loads the parquet files and returns a pandas dataframe.
- The pipeline can only be started manually at the moment, so there is no schedule_interval
- In the first task, the table is deleted completely, this is to prevent possible data duplicates if the pipeline is started several times.
- All parquet files to be loaded are added to a list, automating this step has unfortunately led to zombie jobs in Airflow.
- Tasks are dynamically created to load the data from Parquet files into MySQL, with each task assigned a unique task ID and configured to execute the load_data_to_mysql Python callable function with specific arguments using op_kwargs.


#### Execution ####
   - The pipeline can be started manually in Airflow [localhost:8080 VS Code port forwarding](http://localhost:8080/dags/TLC_Trip_Record/grid)
   - It took almost two and a half hours to load the 12 parquet files.
   - In Airflow it is easy to monitor the progress of the data pipeline

![DAG_RUN](https://github.com/kevinbullock89/new_york_taxi/assets/126856865/941e5064-00ad-41d9-88a5-16622b7f6ad4)


## Data Model

The tables contain a prefix f_ or d_ to clearly identify them as facts or dimension tables. The data is loaded into the fact table f_TaxiData. The data is loaded from the Airflow into the fact table f_TaxiData. The data for the dimensions is stored manually in views, the data itself comes from this website [Data Dictionary – Yellow Taxi Trip Records](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf)

There are two columns in the Datetime type tpep_pickup_datetime and tpep_dropoff_datetime. Two date dimensions are created in Power BI.

### Fact Tables

     ```sh
        CREATE TABLE `f_TaxiData` (
        `my_row_id` bigint unsigned NOT NULL AUTO_INCREMENT /*!80023 INVISIBLE */,
        `VendorID` bigint DEFAULT NULL,
        `tpep_pickup_datetime` datetime DEFAULT NULL,
        `tpep_dropoff_datetime` datetime DEFAULT NULL,
        `passenger_count` double DEFAULT NULL,
        `trip_distance` double DEFAULT NULL,
        `RatecodeID` double DEFAULT NULL,
        `store_and_fwd_flag` text,
        `PULocationID` bigint DEFAULT NULL,
        `DOLocationID` bigint DEFAULT NULL,
        `payment_type` bigint DEFAULT NULL,
        `fare_amount` double DEFAULT NULL,
        `extra` double DEFAULT NULL,
        `mta_tax` double DEFAULT NULL,
        `tip_amount` double DEFAULT NULL,
        `tolls_amount` double DEFAULT NULL,
        `improvement_surcharge` double DEFAULT NULL,
        `total_amount` double DEFAULT NULL,
        `congestion_surcharge` double DEFAULT NULL,
        `airport_fee` double DEFAULT NULL,
        PRIMARY KEY (`my_row_id`)
        ) ENGINE=InnoDB AUTO_INCREMENT=15000937 DEFAULT CHARSET=utf8mb3;
        ```
### Dimension Views

Vendor:

    ```sh
        create or replace view vw_d_Vendor
        as 
        select 
        1 as VendorId, 'Creative Mobile Technologies, LLC' as VendorDescription
        union all
        select
        2 as VendorId, 'VeriFone Inc' as VendorDescription;
```

Rate:

    ```sh
        create or replace view vw_d_Rate 
        as 
        select 
        1 as RateCodeID, 'Standard rate' as RateCodeDescription
        union all
        select
        2 as RateCodeID, 'JFK' as RateCodeDescription
        union all
        select
        3 as RateCodeID, 'Newark' as RateCodeDescription
        union all
        select
        4 as RateCodeID, 'Nassau or Westchester' as RateCodeDescription
        union all
        select
        5 as RateCodeID, 'Negotiated fare' as RateCodeDescription
        union all
        select
        6  as RateCodeID, 'Group ride' as RateCodeDescription;
```

Store and forward trip:

    ```sh
        create or replace view vw_d_StoreForwardTrip
        as 
        select 
        'Y' as Store_and_fwd_flag, 'store and forward trip' as Store_and_fwd_flag_description
        union all 
        select 
        'N' as Store_and_fwd_flag, 'not a store and forward trip' as Store_and_fwd_flag_description;
    ```

Payment type:

    ```sh
        create or replace view vw_d_PaymentType
        as 
        select 
        1 as PaymentType, 'Credit Card' as PaymentTypeDescription
        union
        select
        2 as PaymentType, 'Cash' as PaymentTypeDescription
        union
        select
        3 as PaymentType, 'No charge' as PaymentTypeDescription
        union
        select
        4 as PaymentType, 'Dispute' as PaymentTypeDescription
        union
        select
        5 as PaymentType, 'Unknown' as PaymentTypeDescription
        union
        select
        6 as PaymentType, 'Voided trip' as PaymentTypeDescription;
    ```    

### Date Dimension in Power BI

This Power BI query generates a date table named "Drop_off_DateTable" and "Pickup_DateTable" containing a series of dates ranging from the minimum to the maximum date values found in the "tpep_dropoff_datetime" and "tpep_pickup_datetime" column of the 'f_taxidata' table.

1. **Create tables:**

   ```sh
   Drop_off_DateTable = GENERATESERIES(MIN('airflow f_taxidata'[tpep_dropoff_datetime]), MAX('airflow f_taxidata'[tpep_dropoff_datetime]))
``` 

   ```sh
   Pickup_DateTable = GENERATESERIES(MIN('airflow f_taxidata'[tpep_pickup_datetime]), MAX('airflow f_taxidata'[tpep_pickup_datetime]))
``` 

2. **Adding column:**

This code creates a column for the day, month and year. This makes it easier to use this as a filter in Power BI.

   ```sh
   Day = DAY('Drop_off_DateTable'[Datetime])
   Month = MONTH('Drop_off_DateTable'[Datetime].[Date])
   Year = YEAR('Drop_off_DateTable'[Datetime])
``` 
   ```sh
   Day = DAY('Pickup_DateTable'[Datetime])
   Month = MONTH('Pickup_DateTable'[Datetime])
   Year = YEAR('Pickup_DateTable'[Datetime])
``` 


### Exploring the Dataset and Data Model

In this section, I show the data model created and analyze the loaded data:

1. **Dataset Exploration:**

There are currently 30.904.308 rows in the table.

![count](https://github.com/kevinbullock89/new_york_taxi/assets/126856865/412f1c32-dfd4-4fd2-8edd-f29758118c71)


```sh
    select count(*) from f_taxidata;
``` 


This SQL script retrieves aggregated statistics from a table named f_taxidata. It calculates the total fare amount, total passenger count, total travel time in hours, average travel time per passenger in hours, and average travel time per passenger in minutes for each month and year. The results are grouped by month and year of the pickup datetime and ordered in ascending order based on the year and month. 

```sh
    SELECT year(tpep_pickup_datetime) AS year
        ,month(tpep_pickup_datetime) AS month
        ,sum(fare_amount) AS total_fare_amount
        ,sum(passenger_count) AS total_passenger_count
        ,sum(TIMESTAMPDIFF(HOUR, tpep_pickup_datetime, tpep_dropoff_datetime)) AS total_travel_time_hours
        ,sum(TIMESTAMPDIFF(HOUR, tpep_pickup_datetime, tpep_dropoff_datetime)) / SUM(passenger_count) AS avg_travel_time_per_passenger_per_hours
        ,sum(TIMESTAMPDIFF(minute, tpep_pickup_datetime, tpep_dropoff_datetime)) / SUM(passenger_count) AS avg_travel_time_per_passenger_per_minute
    FROM f_taxidata ft 
    GROUP BY month(tpep_pickup_datetime)
        ,year(tpep_pickup_datetime)
    ORDER BY year(tpep_pickup_datetime) ASC
        ,month(tpep_pickup_datetime) ASC
``` 

The result shows that there are problems with the data quality. The result is stored in the Exploring_Data.png file. It shows us that there are taxi drives that have not been driven as expected in 2021. Particularly strange are those that are to be driven in the future.


![Exploring_Data](https://github.com/kevinbullock89/new_york_taxi/assets/126856865/9016ac26-9abb-45e9-be74-3345e2627176)



2. **Data Model Description:**
   - There is one fact table and six dimension table, these always have an m:1 relationship, which is optimal for analyses.
   - This model allows you to create complex reports in Power BI
  
![PowerBI_Data_Model](https://github.com/kevinbullock89/new_york_taxi/assets/126856865/d495a6be-9be5-4e1a-a42b-ba15e1c5aad8)
 

## Possible Next Steps

After three days of completion, consider the following next steps:

1. **Performance Optimization:**
   - Since the loading of the data takes a long time, it could be a possibility to increase the size of the VM and the mysql server. However, this will also increase the costs

2. **Advanced Analytics:**
   - Explore advanced analytics or machine learning techniques to derive further insights from the taxi data

3. **Visualization:**
   - Creation of reports in Power BI with proper visualizations

4. **Automatic loading of parquet files:**
   - The files are currently loaded manually from the website, it might be possible to do this with a python script

5. **Enable Scheduler:**
    - The aim should be to load a new file with cab data automatically as soon as it is available. It is not necessary to load historical data, only the newly added data. 

6. **Data cleaning:**
    - It has been shown that the quality of the data is sometimes not very good, as there are taxi trips that were made in a different year (or in the future). An additional function could be created that checks whether the data in the parquet file really belongs to this month based on the month in the parquet file name. 

7. **Hash function:**
    - The relationship in Power from the dimension tables to the fact table should ideally be an integer. In some cases, however, the tables are linked via string or datetime columns, which can lead to performance problems. A hash function in python could create a hash value for these columns, which can then also be used in Power BI to join the tables.

8. **Error notification:**
    - If a pipeline fails, an e-mail from an SMTP Server can be sent to the Data Engineers.

9. **GitHub and CI/CD Process:**
    - The code should be stored in a repository
    - A CI/CD process should be defined for deployment on different environments.
