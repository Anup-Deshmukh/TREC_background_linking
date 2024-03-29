#!/usr/bin/python3

import xml.sax


topics = []


class XmlHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.tag = ""
        self.num = ""
        self.docid = ""
        self.url = ""
        self.title = ""
        self.desc = ""
        self.narr = ""
        self.subtopics = []
        self.entities = []
        self.emp = {}

    # Call when an element starts
    def startElement(self, tag, attributes):
        self.tag = tag
        if self.tag == "top":
            1
            # print("*****Topic*****")
        elif self.tag == "entities":
            1
            # print("=====Entities=====")
        elif self.tag == "subtopics":
            self.subtopics = []

    # Call when an elements ends
    def endElement(self, tag):
        if self.tag == "num":
            1
            # print("num:", self.num)
        elif self.tag == "docid":
            1
            # print("docid:", self.docid)
        elif self.tag == "url":
            1
            # print("url:", self.url)
        elif tag == "entity":
            self.entities.append(self.emp)
            # print(self.emp)
            self.emp = {}
        elif tag == "sub":
            self.subtopics.append(self.sub)
        elif tag == "top":
            mp = {}
            mp['num'] = self.num
            mp['docid'] = self.docid
            mp['url'] = self.url
            mp['title'] = self.title
            mp['desc'] = self.desc
            mp['narr'] = self.narr
            mp['subtopics'] = self.subtopics
            mp['entities'] = self.entities
            topics.append(mp)
            # print("------------------ TOPICS HERE: ", topics)
        self.tag = ""

    # Call when a character is read
    def characters(self, content):
        if self.tag == "num":
            self.num = content
        elif self.tag == "docid":
            self.docid = content
        elif self.tag == "url":
            self.url = content
        elif self.tag == "title":
            self.title = content
        elif self.tag == "desc":
            self.desc = content
        elif self.tag == "narr":
            self.narr = content
        elif self.tag == "sub":
            self.sub = content
        elif self.tag == "id" or self.tag == 'mention' or self.tag == 'link':
            self.emp[self.tag] = content


def get_topics(filename):
    # create an XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # override the default ContextHandler
    Handler = XmlHandler()
    parser.setContentHandler(Handler)

    parser.parse(filename)
    # parser.parse(filename)

    return topics


if __name__ == "__main__":

    # create an XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # override the default ContextHandler
    Handler = XmlHandler()
    parser.setContentHandler(Handler)

    parser.parse("/Users/udhavsethi/dev/ref/TREC_background_linking/wapo/WashingtonPost/data/newsir21-topics.txt")
    # parser.parse("E:/Track/WashingtonPost.v2/data/newsir18-entities.txt")


