import requests
import random
from bs4 import BeautifulSoup # type: ignore
from typing import Any
from customAgents.agent_tools import ScrapeStaticLinkTool


class SearchTool(ScrapeStaticLinkTool):
    def __init__(
            self,
            description: str = "Tool used to search the internet",
            tool_name: str = None,
            max_num_chars: int = 5000,
            num_top_results: int = 1,
            get_content_only: bool = True,
            save_last_search_links_path: str = None
            ):
        
        self.num_top_results = num_top_results
        self.get_content_only = get_content_only
        self.save_last_search_links_path = save_last_search_links_path
        self.user_agents = [
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/91.0.4472.114 Safari/537.36",
                    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Debian; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Arch Linux; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/90.0.4430.212 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux Mint; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; openSUSE; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; CentOS; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Gentoo; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Manjaro; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Pop!_OS; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Kali Linux; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 OPR/77.0.4054.172",
                    "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 OPR/77.0.4054.172"
                ]
        
        super().__init__(description, tool_name, max_num_chars)


    def execute_func(self, query: str) -> str:
        
        search_results = self._make_search(query=query)
        summarized_results = []
        full_text_content = ''

        if self.save_last_search_links_path is not None:
            search_results_txt = 'Search Results : \n\n'
            for result in search_results[:self.num_top_results]:
                search_results_txt += f"Link: {result['link']}\n\n"

            with open(self.save_last_search_links_path,'w') as f:
                f.write(search_results_txt)
        
        for result in search_results[:self.num_top_results]:  
            content = self._fetch_url_content(url=result["link"])
            summarized_results.append({"title": result["title"], "link": result["link"], "content": content})
            full_text_content += content

        if self.get_content_only:
            return str(full_text_content)
        else:
            return summarized_results


    def _fetch_url_content(self, url: str) -> Any:
        return super().execute_func(url)
    

    def _make_search(self, query: str) -> Any:

        url = f"https://duckduckgo.com/html/?q={query}"
        headers = {
            "User-Agent": random.choice(self.user_agents)
            }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for result in soup.find_all("a", {"class", "result__url"}):
            title = result.get_text()
            link = result['href']
            if link.startswith('/'):
                link = 'https://duckduckgo.com' + link
            results.append({"title": title, "link": link})
            
        return results
    
