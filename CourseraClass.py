"""
@author: Daniel Firebanks
@usage: See scrape_coursera_reviews.py
"""

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json

class CourseraCourse:

    def __init__(self, url, driver, from_json=False):
        """Only requires the URL of the ORIGINAL COURSE PAGE and the driver object, the rest gets taken care of automatically"""

        self.url = url
        print(f"URL is {self.url}")
        self.revs_url = url + "/reviews"

        # Initialize this if the course data is not being loaded from json
        if not from_json:
            self.driver = driver


            self.description, self.score, self.name, self.institution, self.total_reviews, self.total_ratings = get_other_attrs(self.driver, self.url, self.revs_url)

            self.driver.get(self.revs_url)

            # {Number of stars: List of all reviews with those stars}
            self.reviews_dict = dict()
            self.all_reviews = []

            # Number of reviews we have
            self.num_reviews = 0

            self.df = None
            self.json = None
        else:
            self.name = None
            self.score = None
            self.description = None
            self.institution = None
            self.total_ratings = None

            # Total reviews that the course has
            self.total_reviews = None

            # {Number of stars: List of all reviews with those stars}
            self.reviews_dict = dict()
            self.all_reviews = []

            # Number of reviews we have
            self.num_reviews = 0

            self.df = None
            self.json = None

    def add_reviews(self, reviews):
        """Takes in a list of reviews, stores all of them and updates the review dictionary for the course"""
        self.all_reviews.extend(reviews)  # Make sure these aren't repeated

        for review in reviews:
            if str(review.stars) not in self.reviews_dict:
                self.reviews_dict[str(review.stars)] = [review]
            else:
                self.reviews_dict[str(review.stars)].append(review)

            self.num_reviews += 1

    def get_info(self):
        """Return course information"""
        print(self.__str__())

    def __str__(self):
        return f"Name: {self.name} \
        \nScore: {self.score} \
        \nInstitution: {self.institution} \
        \nDescription: '{self.description}' \
        \nTotal Ratings: {self.total_ratings} \
        \nTotal Reviews: {self.total_reviews} \
        \nNumber of Reviews Extracted: {self.num_reviews} \n"

    def get_reviews(self, num_pages=None):
        """Extracts num_pages of results from course"""
        c_allrevs = []
        print("Starting to get reviews...")

        # Check if there are top reviews, depending on that the no_reviews_path would change
        top_revs = "rc-TopRatings"
        no_reviews_path = "//*[@id='root']/div[1]/div/div[3]/div[2]/p/span"
        div_index = 3

        try:
            self.driver.find_element_by_class_name(top_revs)
            div_index = 4
        except Exception as e:
            print("No top reviews!")
            check = self.driver.find_element_by_xpath(no_reviews_path).text
            if check == "0 Reviews":
                print(f"{self.name} by {self.institution} has no reviews!")
                return

        # Path to bar of result pages and the xpath location of the ">" (next) button
        resultsbar_path = f"//*[@id='root']/div[1]/div/div[{div_index}]/nav/ul/li"
        resultsbar = list(self.driver.find_elements_by_xpath(resultsbar_path))
        next_button = len(resultsbar)

        # Get the first page of reviews
        c_allrevs.extend(extract_reviews(self.driver.page_source))
        pnum = 1

        # If we want all reviews
        if not num_pages:
            # We want the second to last element, which represents the number of the last page of results
            try:
                lastpagebutton_path = \
                    f"//*[@id='root']/div[1]/div/div[{div_index}]/nav/ul/li[{next_button-1}]/button/span"
                num_pages = self.driver.find_element_by_xpath(lastpagebutton_path).text
                print(f"Total number of page results is {num_pages}")
                num_pages = int(num_pages)
            except:
                # If the above didn't work, then there is not more than one page of reviews
                num_pages = 1
                print("Total number of page results is 1")

        if num_pages != 1:
            # Get all the rest
            for i in range(1, num_pages):
                pnum += 1
                c_allrevs.extend(extract_reviews(click_next_page(self.driver, pnum, div_index, next_button)))

        self.add_reviews(c_allrevs)

    def has_reviews(self):
        if len(self.all_reviews) != 0:
            return True
        print("No reviews found!")
        return False

    def print_some_reviews(self, num):
        """Prints num reviews"""
        if self.has_reviews():
            for i in range(num):
                print(self.all_reviews[i])

    def build_reviews_df(self):
        """Builds pandas dataframe of reviews given review objects"""
        columns = ["Review Text", "Number of Stars", "Date of Review"]
        self.df = pd.DataFrame(columns=columns, index=(range(self.num_reviews)))

        if self.has_reviews():
            for i in range(self.num_reviews):
                rev = self.all_reviews[i]
                series = pd.Series([rev.text, rev.stars, rev.date])
                self.df.iloc[i, :] = series.values

    def export_reviews_df(self, file_path):
        """Converts pandas dataframe to csv and stores it in specified path"""
        if self.has_reviews():
            self.df.to_csv(file_path + self.name + "-" + self.institution + "-reviews.csv")

    def build_course_json(self, file_path=None):
        """Builds a JSON object containing all CourseraCourse attributes, and stores it in a json file if given file_path"""
        if self.has_reviews():
            data = {"Name": self.name,
                    "Institution": self.institution,
                    "Description": self.description,
                    "Score": self.score,
                    "URL": self.url,
                    "Reviews URL": self.revs_url,
                    "All Reviews": self.df.to_json(),
                    #"Reviews by category": self.reviews_dict,
                    "Number of reviews we have": self.num_reviews,
                    "Total number of reviews on page": self.total_reviews,
                    "Total number of ratings on page": self.total_ratings}

            if file_path:
                with open(file_path + self.name + "-" + self.institution + "json-obj.json", "w") as outfile:
                    json.dump(data, outfile)
            else:
                self.json = json.dumps(data)


class Review:
    def __init__(self, stars, text, date):
        self.stars = stars
        self.text = text
        self.date = date

    def __str__(self):
        return f"Number of Stars: {self.stars} \
        \nDate of Review: {self.date} \
        \nText of Review: '{self.text}'\n"

""" HELPER JSON FUNCTION!!!!!!!!"""

def unpack_json(json_file):
    """Returns a CourseraCourse object given a JSON file"""

    try:
        with open(json_file) as infile:
            data = json.load(infile)
            course = CourseraCourse(data["URL"], from_json=True)
            course.name = data["Name"]
            course.description = data["Description"]
            course.institution = data["Institution"]
            course.score = data["Score"]
            course.reviews_dict = json.load(data["Reviews by category"])
            course.all_reviews = list(course.reviews_dict.values())
            course.num_reviews = data["Number of reviews we have"]
            course.total_reviews = data["Total number of reviews on page"]
            course.total_ratings = data["Total number of ratings on page"]
            return course
    except Exception as e:
        print("Please insert a valid JSON file type!")
        print(e)

""" HELPER DRIVER FUNCTIONS BELOW!!!!!!!"""

def extract_reviews(page_link):
    """Given a reviews page link, it extracts all the reviews on that single result page"""
    soup = BeautifulSoup(page_link, "lxml")

    # Get the wrapper of all the the reviews from that page
    results = list(soup.find_all("div", attrs={"class": "review"}))

    # Iterate through results in one page and create list of review objects
    review_list = []

    for result in results:
        rev_wrap = result.contents[0]
        rev_text = rev_wrap.find_all("div", attrs={"class": "reviewText"})[0].text
        rev_date = rev_wrap.find_all("p", attrs={"class": "dateOfReview"})[0].text

        rev_stars_wrap = rev_wrap.find_all("label")
        rev_stars = 0
        for tag in rev_stars_wrap:
            if "Filled Star" in tag.text:
                rev_stars += 1

        review_list.append(Review(rev_stars, rev_text, rev_date))

    return review_list


def get_other_attrs(driver, norm_url, revs_url):
    """Gets all attributes of a course, given a driver with an opened page link"""
    about, score, name, inst, total_revs, total_ratings = "", 0, "", "", 0, 0

    print("Getting other attributes...")

    driver.get(norm_url)

    # Get the name and institution
    try:
        name_path = "//*[@id='root']/div[1]/div/div[1]/div[1]/div[1]/div/div/div[1]/div[2]/h1"
        name = driver.find_element_by_xpath(name_path).text.replace("/", "")

        # 2 cases -> If we have the image of the institution, or if we dont
        inst_path = "//*[@id='root']/div[1]/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div[2]/img"
        alt_inst_path = "//*[@id='root']/div[1]/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div[2]/span"
        try:
            inst = driver.find_element_by_xpath(inst_path).get_attribute("title").replace("/", "")
        except:
            inst = driver.find_element_by_xpath(alt_inst_path).text
    except:
        print("Couldn't find name/institution!")

    driver.get(revs_url)

    # Click the "VIEW ALL" button to get all description first
    try:
        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH,
                                                                          "//*[@id='root']/div[1]/div/div[2]/div/div/span/span[1]/span/span/span/button")))
        viewall_button = driver.find_element_by_xpath("//*[@id='root']/div[1]/div/div[2]/div/div/span/span[1]/span/span/span/button")

        if viewall_button:
            viewall_button.click()
    except:
        print("No VIEW ALL button!")

    # Check if there are any reviews
    try:
        total_revs = \
            driver.find_element_by_xpath("//*[@id='root']/div[1]/div/div[1]/div/div[2]/div[3]/div[2]/span").text.split(
                " ")[
                0]
        total_ratings = \
            driver.find_element_by_xpath("//*[@id='root']/div[1]/div/div[1]/div/div[2]/div[2]/span").text.split(" ")[0]
        score = driver.find_element_by_xpath("//*[@id='root']/div[1]/div/div[1]/div/div[2]/span").text
    except Exception as e:
        print("Possibly no reviews found!")

    # Get the description of the course
    try:
        about = driver.find_element_by_xpath("//*[@id='root']/div[1]/div/div[2]/div/div/span[1]/span[1]").text

    except Exception as e:
        print("Couldn't find description!!!")

    print("Success in getting other attributes!")

    return about, score, name, inst, total_revs, total_ratings


def click_next_page(driver, page_num, div_index, next_button):
    """Click the next page of results, return resulting html"""

    button_path = f"//*[@id='root']/div[1]/div/div[{div_index}]/nav/ul/li[{next_button}]/button"
    driver.find_element_by_xpath(button_path).click()
    print(f"Loading page {page_num}...")

    # Wait until the results load, this should be adjusted depending on the internet speed
    try:
        WebDriverWait(driver, 45).until(EC.visibility_of_element_located((By.XPATH,
                                                                          f"//*[@id='root']/div[1]/div/div[{div_index}]/div[2]/p/span")))
        print("Got it!")
        print()
        return driver.page_source

    except:
        print(f"Result page {page_num} did not load, moving on to the next one...")
        # TODO In the preprocessing, we must check if there are review duplicates!
        click_next_page(driver, page_num+1, div_index, next_button)

