import psycopg2
from psycopg2.extras import RealDictCursor


hostname = 'localhost'
database = "demo"
username = 'postgres'
pwd = 'A1@arpit'
port_id = 5432
curr,conn = None,None


try:
    
    conn = psycopg2.connect(
        host= hostname,
        dbname = database,
        user = username,
        port = port_id,
        password = pwd    
    )
    curr = conn.cursor(cursor_factory= RealDictCursor)
    
    curr.execute('DROP TABLE IF EXISTS Personal')
    create_table = '''
    CREATE TABLE IF NOT EXISTS Personal (
    Student_id SMALLINT NOT NULL UNIQUE,
    Name VARCHAR(30) NOT NULL,
    Age INT NOT NULL CHECK (Age >= 18),
    Gender VARCHAR(10),
    City TEXT NOT NULL DEFAULT 'Jaipur',
    PRIMARY KEY (Student_id)
    );
    '''
    curr.execute(create_table)
    conn.commit()
    
    # insert_script = '''
    # INSERT INTO Personal (Student_id,Name,Age,Gender,City)
    # VALUES
    # (1004,'ARPIT AKAR',31,'M','Jaipur'),
    # (2305,'SHELLY GUPTA',27,'F','Alwar'); 
    # '''
    # curr.execute(insert_script)
    # conn.commit()
    
    query = '''
    INSERT INTO Personal
    (Student_id, Name, Age, Gender, City)
    VALUES (%s, %s, %s, %s, %s)
    '''

    # Line 8
    data = [(1991, 'RISHABH AKAR', 34, 'M', 'Jaipur'),
            (2305,'SHELLY GUPTA',27,'F','Alwar'),
            (1004,'ARPIT AKAR',31,'M','Jaipur')]

    # Line 11
    curr.executemany(query, data)

    
    # print(curr.fetchall())
    # PostgreSQL automatically converts column names to lowercase unless quoted.
    
    
    
    update_script = 'UPDATE Personal SET Age= Round(Age* 0.9) where Gender=%s'
    update_record = ('F',)
    curr.execute(update_script,update_record)
    
    
    curr.execute('SELECT * FROM Personal')
    for record in curr.fetchall():
        print(record['name'],record['age'])
    # Line 13
    conn.commit()
except Exception as e:
    print(e)
finally:
    if curr is not None: 
        curr.close()
    if conn is not None:
        conn.close()