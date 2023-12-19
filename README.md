# day97-online-store
A simple online store using Flask, Bootstrap, JQuery, SQLAlchemy, and Stripe's API, with data currently stored on a sqlite database. Loosely based on a old Spring Framework personal project, but with a different example premise.
Done as part of the 100 Days of Code: The Complete Python Pro Bootcamp for 2023 course, [link here]([https://www.udemy.com/course/100-days-of-code/learn/practice/1251204#overview](https://www.udemy.com/course/100-days-of-code/))

All components required, including a requirments.txt for the modules used, and the store.db (the generated sqlite database) have been included. Secret keys, APIs, and other sensitive data are left in "as-is" to show work, with the understanding that production deployed servers would have these variables stored as environment variables. None of this data provided here is valuable, as it's either public demo keys or throwaway accounts.

Please note that this project only works so far as to allow for a minimally viable demonstration of the website's features and functions, and does not include robust validation or authentication at all. The embedded Stripe checkout session is left in "test mode" since adding a live or test key here for a barebones store would be foolish and open up a personal security risk.
To use the Stripe checkout functionality, please use the card "4242 4242 4242 4242", or any other Stripe-provided test credit card details to check the functionality of the test embed.

This project will be polished in increments, but the basic usage loop of the online is there for display, however messy it may be.
People who would like to, for some reason unknown to me or common sense, use this in a live setting should note that this is **very** unsecure, and should be made more secure to modern web security threats, as well as providing more robust input validation, and a superior authentication system beyond "you are either logged in or not" and "you have this role, so access is limited".
