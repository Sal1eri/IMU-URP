# IMU-URP
This is a Python script that allow Inner Mongolia University students to automatically check their course schedule from the university's URP system. The script uses the `requests` library to handle HTTP requests.



Use the following command to install the required libraries:
```
pip install -r requirements.txt
```

It Mainly used for selecting courses, but it can also be used to check the course schedule and other information related to the courses. 

This Script is for educational purposes only, and should not be used for any malicious activities. Please use it responsibly and do not overload the URP system with too many requests.

There have some shortcomings in this script, You can modify it as follows to make it more efficient and user-friendly:
1. Add Machine Learning Model or sth else to recognize the captcha, so that it can automatically login without manual input.
2. Add a GUI interface to make it more user-friendly. This can be done using libraries such as Tkinter or PyQt. It make the student who are not familiar with programming can also use it easily.
3. Make sure the requests interval is reasonable, to avoid overloading the URP system and getting blocked. You can use the `time` library to add a delay between requests.
4. Add Student Course Score, so that students can check the rank of their course score in the class, and also can check the average score of the class.
5. Make the user information more secure, such as using environment variables or a configuration file to store the student ID and password, instead of hardcoding them in the script. This can help prevent unauthorized access to the student's account.

