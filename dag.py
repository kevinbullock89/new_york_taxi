        from datetime import datetime, timedelta
        from airflow import DAG
        from airflow.providers.mysql.operators.mysql import MySqlOperator
        from airflow.operators.python import PythonOperator
        from airflow.providers.mysql.hooks.mysql import MySqlHook
        import pandas as pd
        import os

        default_args = {
            'owner': 'Kevin',
            'retries': 1,
            'retry_delay': timedelta(seconds=2)
        }

        def load_data_to_mysql(ds, func, parquet_file, **kwargs):
            try:
                # Retrieve the data from the specified function
                df = func(parquet_file)

                # Create a connection to the MySQL database
                hook = MySqlHook(mysql_conn_id='mysql_airflow')
                engine = hook.get_sqlalchemy_engine()

                # Use pandas to load the data into the MySQL database
                table_name = 'f_taxidata'
                df.to_sql(name=table_name, con=engine, if_exists='append', index=False)
                
                # print statement for the logging
                print(f"Data loaded successfully from {parquet_file}")
            except Exception as e:
                print(f"Error loading data from {parquet_file}: {str(e)}")
                raise

        def taxi_data_from_parquet(parquet_file):
            # The parquet file is returned as pandas dataframe.
            df = pd.read_parquet(parquet_file)
            return df

        dag_id = 'TLC_Trip_Record'
        start_date = datetime(2024, 1, 10, 2)
        schedule_interval = None  # Set to None to disable scheduling

        with DAG(
            dag_id=dag_id,
            default_args=default_args,
            description='mysql_dag',
            start_date=start_date,
            schedule_interval=schedule_interval
        ) as dag:
            # Task to truncate the MySQL table
            truncate_task = MySqlOperator(
                task_id='Truncate_MySQL_Table',
                mysql_conn_id='mysql_airflow',
                sql="TRUNCATE TABLE f_taxidata;"
            )

            # Add the files to a list. Currently all files from 2021
            parquet_files = ['/data/yellow_tripdata_2021-01.parquet',
                            '/data/yellow_tripdata_2021-02.parquet',
                            '/data/yellow_tripdata_2021-03.parquet',
                            '/data/yellow_tripdata_2021-04.parquet',
                            '/data/yellow_tripdata_2021-05.parquet',
                            '/data/yellow_tripdata_2021-06.parquet',
                            '/data/yellow_tripdata_2021-07.parquet',
                            '/data/yellow_tripdata_2021-08.parquet',
                            '/data/yellow_tripdata_2021-09.parquet',
                            '/data/yellow_tripdata_2021-10.parquet',
                            '/data/yellow_tripdata_2021-11.parquet',
                            '/data/yellow_tripdata_2021-12.parquet']
            
            # The automated loading of all files into a list unfortunately did not work, error message in Airflow: ERROR - Detected zombie job
            # parquet_directory = '/data/'  # Specify the directory containing parquet files
            # parquet_files = [os.path.join(parquet_directory, file) for file in os.listdir(parquet_directory) if file.endswith('.parquet')]
            

            # First task delete all data and then load the parquet files into the mysql table
            tasks = [truncate_task]
            # Dynamic task generation for each parquet file
            for i, parquet_file in enumerate(parquet_files, start=1):
                task_id = f'Load_Taxi_Data_to_mysql_{i}'
                load_task = PythonOperator(
                    task_id=task_id,
                    python_callable=load_data_to_mysql,
                    op_kwargs={
                        'func': taxi_data_from_parquet,
                        'parquet_file': parquet_file
                    },
                )
                truncate_task >> load_task  # Set dependency to truncate_task
                tasks.append(load_task)

            # Set task dependencies for loading tasks
            for i in range(len(tasks) - 1):
                tasks[i] >> tasks[i + 1]
