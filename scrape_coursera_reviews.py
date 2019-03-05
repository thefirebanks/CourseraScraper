"""
@author: Daniel Firebanks
@usage: Example application of CourseraClass to extract reviews from Coursera
"""
from CourseraClass import CourseraCourse
from selenium import webdriver

def main():
    """ Extracts reviews given a file of URLs belonging to each subject category, HOWEVER this process must
        be monitored closely because sometimes the course website returns different content than what expected
        such as redirecting to a sign up page or the facebook page. Nevertheless, it should work"""

    subjects = ["Data_Science", "Business", "Computer_Science", "Arts_and_Humanities", "Social_Sciences", \
                "Language_Learning", "Health", "Personal_Development", "Physical_Sciences_and_Engineering", \
                "Life_Sciences"]

    ### CODE FOR MULTIPLE URLS --> after having run scrape_coursera_urls.py
    url_file = "~/Course_URLS/" + subjects[0] + "_urls.txt"
    with open(url_file, "r") as infile:
        all_urls = infile.readlines()
        driver = webdriver.Chrome("driver_path")  # Write the path of your own driver
        for course_url in all_urls:
            course = CourseraCourse(course_url, driver)
            course.get_info()
            course.get_reviews()
            # course.print_some_reviews()
            if course.has_reviews():
                course.build_reviews_df()
                course.export_reviews_df(file_path="~/Reviews/" + subjects[0] + "_Reviews/")
                course.build_course_json(file_path="~/JSON_files/" + subjects[0] + "_JSON/")
        driver.quit()

    ### CODE FOR ONE URL
    # course_url = "https://www.coursera.org/learn/python-data-analysis"
    # driver = webdriver.Chrome("driver_path")  
    # course = CourseraCourse(course_url, driver)
    # course.get_info()
    # course.get_reviews()
    # if course.has_reviews():
    #   course.print_some_reviews()
    #   course.build_reviews_df()
    #   course.export_reviews_df(file_path="/Reviews")
    #   course.build_course_json(file_path="")
    # driver.quit()

    

main()
