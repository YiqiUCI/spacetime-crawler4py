
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urldefrag, urljoin
from collections import defaultdict


# variables used for the report_output function
UniqueURLs = set()
SubdomainURLs = defaultdict(set)
WordFreq = {}
longest_page = ("", 0)  # (url, word_count)

# list of stop words we plan to use
STOPWORDS = {
    "a","about","above","after","again","against","all","am","an","and","any",
    "are","aren't","as","at","be","because","been","before","being","below",
    "between","both","but","by","can't","cannot","could","couldn't","did",
    "didn't","do","does","doesn't","doing","don't","down","during","each",
    "few","for","from","further","had","hadn't","has","hasn't","have",
    "haven't","having","he","he'd","he'll","he's","her","here","here's",
    "hers","herself","him","himself","his","how","how's","i","i'd","i'll",
    "i'm","i've","if","in","into","is","isn't","it","it's","its","itself",
    "let's","me","more","most","mustn't","my","myself","no","nor","not","of",
    "off","on","once","only","or","other","ought","our","ours","ourselves",
    "out","over","own","same","shan't","she","she'd","she'll","she's",
    "should","shouldn't","so","some","such","than","that","that's","the",
    "their","theirs","them","themselves","then","there","there's","these",
    "they","they'd","they'll","they're","they've","this","those","through",
    "to","too","under","until","up","very","was","wasn't","we","we'd","we'll",
    "we're","we've","were","weren't","what","what's","when","when's","where",
    "where's","which","while","who","who's","whom","why","why's","with",
    "won't","would","wouldn't","you","you'd","you'll","you're","you've",
    "your","yours","yourself","yourselves"
}

def scraper(url, resp):
    # Track unique URLs
    clean_url, _ = urldefrag(url)
    # Track subdomains


    # Extract text and count words
    if resp and resp.status == 200 and resp.raw_response:
        typeH = resp.raw_response.headers.get('Content-Type', "")
        if "text/html" in typeH.lower():
            html = resp.raw_response.content
            if html:
                UniqueURLs.add(clean_url)
                host = urlparse(clean_url).hostname
                if host and host.endswith(".uci.edu"):
                    SubdomainURLs[host].add(clean_url)

                soup = BeautifulSoup(html, "lxml")
                text = soup.get_text(separator=" ").lower()
                words = re.findall(r"[a-z]+(?:'[a-z]+)?", text)
                count = 0
                for w in words:
                    if w not in STOPWORDS:
                        WordFreq[w] = WordFreq.get(w, 0) + 1
                        count += 1

                global longest_page
                if count > longest_page[1]:
                    longest_page = (clean_url, count)
                if len(UniqueURLs) % 200 == 0:
                    print("---- Progress ----")
                    print("Unique pages:", len(UniqueURLs))
                    print("Current longest:", longest_page[0], "-", longest_page[1])
                    print("Subdomains so far:", len(UniqueURLs))
                    print("------------------")


    # go back to normal crawling
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    links =  []
    if resp is None:
        return links


    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the  url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status != 200 or resp.raw_response is None:
        return links
    typeH = resp.raw_response.headers.get('Content-Type',"")
    if "text/html" not in typeH.lower():
        return links
    html = resp.raw_response.content

    if not html:
        return links

    soup = BeautifulSoup(html, "lxml")

    base = resp.url if resp.url else url

    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue

        href = href.strip()
        if href.startswith("#"):
            continue

        if href.startswith("mailto:") or href.startswith("javascript:"):
            continue

        abs_url = urljoin(base, href)
        abs_url, _ = urldefrag(abs_url)
        links.append(abs_url)

    return list(dict.fromkeys(links))

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        host = parsed.hostname
        if host is None:
            return False
        if not (
                host.endswith (".ics.uci.edu") or
                host.endswith(".cs.uci.edu") or
                host.endswith(".informatics.uci.edu") or
                host.endswith(".stat.uci.edu")
        ):
            return False

        if len(url) > 300:
            return False
        if parsed.query.count("&") >= 6:
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

# The report output / summary to the 4 questions
def report_output():
    print("Report Output\n")

    # 1. Unique pages
    print("Number of Unique Pages:", len(UniqueURLs))
    with open("unique_pages.txt", "w") as f:
        f.write(str(len(UniqueURLs)))

    # 2. Longest page
    print("Longest Page:", longest_page[0], "-", longest_page[1], "words")
    with open("longest_page.txt", "w") as f:
        f.write(f"{longest_page[0]} — {longest_page[1]} words")

    # 3. Top 50 words
    print("50 Most Common Words")
    top50 = sorted(WordFreq.items(), key=lambda x: x[1], reverse=True)[:50]
    with open("top50_words.txt", "w") as f:
        for word, freq in top50:
            f.write(f"{word}: {freq}\n")

    # 4. Subdomains
    print("Subdomains found")
    sorted_subdomains = sorted((k, len(v)) for k, v in SubdomainURLs.items())
    with open("subdomains.txt", "w") as f:
        for sub, count in sorted_subdomains:
            f.write(f"{sub}, {count}\n")