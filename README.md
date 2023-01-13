# PaceConverterBot

[*Check out the comments I'm making on Reddit!*](https://www.reddit.com/user/PaceConverterBot/)

**What**: I convert & comment running/cycling paces found in images to their metric/imperial equivalent.

**Why**: For convenience of people used to either system.

**When**: Check for new image posts every 5 minutes. (Reddit Galleries take more time to get processed as Reddit delays the population of correct image order in the JSON by 5~10 mins)

**Where**: Monitor & comment on posts in bunch of activity subs.

**How**: Query the latest JSON of every monitored sub, identify if post contains image/s, use either Google Cloud Vision or AWS Rekognition to do the OCR, regex the pace/s out of the text extracted, convert them, & finally comment.
