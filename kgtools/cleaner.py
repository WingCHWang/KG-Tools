#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
import re
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize

from kgtools.type import Sentence, Doc


class BaseCleaner:
    __name__ = "Cleaner"

    PUNC_TABLE = {ord(zh): ord(en) for zh, en in zip('‘’“”…，。！？【】（）％＃＠＆：',
                                                     '\'\'"".,.!?[]()%#@&:')}

    def __init__(self, rules=None):
        self.rules = rules
        self.root_nodes = {rule["attr"]: rule["value"] for rule in rules if rule["type"] == "root_node"}
        self.removes = {rule["attr"]: rule["value"] for rule in rules if rule["type"] == "remove"}

    def worker(self, html):
        body = BeautifulSoup(html, "lxml").body

        # remove useless elements
        scripts = body.findAll("script")
        [script.extract() for script in scripts]
        noscripts = body.findAll("noscript")
        [noscript.extract() for noscript in noscripts]
        navs = body.findAll(class_=re.compile(r'.*(nav|Nav|footer|Footer).*'))
        [nav.extract() for nav in navs]
        footers = body.findAll("footer")
        [footer.extract() for footer in footers]

        for attr, value in self.removes.items():
            if attr == "tag":
                rms = body.findAll(value)
                [rm.extract() for rm in rms]
            elif attr == "id":
                rms = body.findAll(id=value)
                [rm.extract() for rm in rms]
            elif attr == "class":
                rms = body.findAll(class_=value)
                [rm.extract() for rm in rms]

        roots = []
        for attr, value in self.root_nodes.items():
            if attr == "tag":
                roots.extend(body.findAll(value))
            elif attr == "id":
                roots.extend(body.findAll(id=value))
            elif attr == "class":
                roots.extend(body.findAll(class_=value))
        if len(roots) == 0:
            roots = [body]

        texts = []
        for root in roots:
            for li in root.findAll("li"):
                string = li.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                li.clear()
                li.append(string)
            for h in root.findAll(re.compile(r'h[1-6]')):
                string = h.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                h.clear()
                h.append(string)
            for p in root.findAll("p"):
                string = p.get_text().strip()
                if len(string) > 0 and string[-1] not in set(".?!:;,"):
                    string = string + "."
                p.clear()
                p.append(string)

            for table in root.findAll("table"):
                table.clear()
                table.append("TABMARK")
            for img in root.findAll("img"):
                if not img.get("alt") or len(img["alt"]) == 0:
                    img_alt = "IMGMARK"
                else:
                    img_alt = img["alt"]
                img.insert_after(img_alt)
            for code in root.findAll("code"):
                string = code.get_text().strip()
                if len(string.split()) > 5 or len(string) > 50:
                    string = "CODEMARK"
                code.clear()
                code.append(string)

            for pre in root.findAll("pre"):
                pre.clear()
                pre.append("CODEMARK")
            text = root.get_text()
            text = text.strip() + " "
            text = re.sub(r'(https?://.*?)([^a-zA-Z0-9/]?\s)', r'URLMARK\2', text)
            texts.append(text)
        return texts

    def split_text(self, text):
        text = text.translate(BaseCleaner.PUNC_TABLE)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'({[^{}]*?)(\?)([^{}]*?})', r'\1QMARK$\3', text)
        text = re.sub(r'(\[[^\[\]]*?)(\?)([^\[\]]*?\])', r'\1QMARK$\3', text)
        text = re.sub(r'(\([^()]*?)(\?)([^()]*?\))', r'\1QMARK$\3', text)
        text = re.sub(r'(\<[^<>]*?)(\?)([^<>]*?\>)', r'\1QMARK$\3', text)
        text = re.sub(r'("[^"]*?)(\?)([^"]*?")', r'\1QMARK$\3', text)
        
        text = re.sub(r'({[^{}]*?)(!)([^{}]*?})', r'\1EXMARK$\3', text)
        text = re.sub(r'(\[[^\[\]]*?)(!)([^\[\]]*?\])', r'\1EXMARK$\3', text)
        text = re.sub(r'(\([^()]*?)(!)([^()]*?\))', r'\1EXMARK$\3', text)
        text = re.sub(r'(\<[^<>]*?)(!)([^<>]*?\>)', r'\1EXMARK$\3', text)
        text = re.sub(r'("[^"]*?)(!)([^"]*?")', r'\1EXMARK$\3', text)
        
        text = re.sub(r'({[^{}]*?)(\.)([^{}]*?})', r'\1SMARK$\3', text)
        text = re.sub(r'(\[[^\[\]]*?)(\.)([^\[\]]*?\])', r'\1SMARK$\3', text)
        text = re.sub(r'(\([^()]*?)(\.)([^()]*?\))', r'\1SMARK$\3', text)
        text = re.sub(r'(\<[^<>]*?)(\.)([^<>]*?\>)', r'\1SMARK$\3', text)
        text = re.sub(r'("[^"]*?)(\.)([^"]*?")', r'\1SMARK$\3', text)
        
        text = text.replace("e.g.", "eg$")
        text = text.replace("E.g.", "Eg$")
        text = text.replace("E.G.", "EG$")
        text = text.replace("i.e.", "ie$")
        text = text.replace("I.e.", "Ie$")
        text = text.replace("I.E.", "IE$")
        sentences = []
        for sent in sent_tokenize(text):
            if self.__pre_check(sent):
                sent_text = sent.replace("eg$", "e.g.").replace("Eg$", "E.g.").replace("EG$", "E.G.").replace("ie$", "i.e.").replace("Ie$", "I.e.").replace("IE$", "I.E.").replace("QMARK$", "?").replace("EXMARK$", "!").replace("SMARK$", ".")
                sent_text = re.sub(r'^(CODEMARK |TABMARK |IMGMARK |URLMARK )(.*)', r'\2', sent_text)
                sent_text = re.sub(r'^(\()(.*)(\))$', r'\2', sent_text)
                sent_text = re.sub(r'^(\[)(.*)(\])$', r'\2', sent_text)
                sent_text = re.sub(r'^({)(.*)(})$', r'\2', sent_text)
                words = sent_text.split()
                if re.search(r'^[^A-Z]', words[0]) is not None and words[1] in {"A", "An", "The", "This", "That", "You", "We"} and re.search(r'^[^A-Z]', words[2]) is None:
                    sent_text = " ".join(words[1:])
                sent_text = sent_text.strip()
                if self.__post_check(sent_text):
                    sentences.append(Sentence(sent_text))
        # text = re.sub(r'\n(.+?[^.?!])\n([A-Z])', r'\n\n\2', text)
        # text = re.sub(r'\s+', " ", text.strip())
        # text = re.sub(r'([?!.]+) ', r'\1\n', text)
        # sentences = set(text.split("\n"))
        return sentences

    def __pre_check(self, sentence):
        if len(sentence) == 0 or not (5 <= len(sentence.split()) <= 200):
            return False
        # check chinese
        if any(["\u4e00" <= ch <= "\u9fff" for ch in sentence]):
            return False
        return True

    def __post_check(self, sentence):
        if re.search(r'^[0-9a-zA-Z"\'<(]', sentence) is None:
            return False
        if sentence.count('[') != sentence.count(']'):
            return False
        if sentence.count('(') != sentence.count(')'):
            return False
        if sentence.count('{') != sentence.count('}'):
            return False
        if sentence.count('"') != sentence.count('"'):
            return False
        if sentence.count(':') > 3 or sentence.count('=') > 3 or sentence.count('[') > 3 or sentence.count('{') > 3:
            return False
        return True

    def clean(self, htmls):
        docs = set()
        sent2sent = {}
        for url, html in htmls:
            texts = self.worker(html)
            sents = []
            for text in texts:
                sents.extend(self.split_text(text))
            if len(sents) > 0:
                docs.add(Doc(url, sents))
                for sent in sents:
                    if sent in sent2sent:
                        new_sent = sent + sent2sent.pop(sent)
                        sent2sent[new_sent] = new_sent
                    else:
                        sent2sent[sent] = sent
        # sent_dict = {}
        # for doc in docs:
        #     for sent in self.split_text(doc.text):
        #         if not self.check_sentence(sent):
        #             continue
        #         if sent in sent_dict:
        #             sent_dict[sent].doc.add(doc)
        #         else:
        #             sent_dict[sent] = Sentence(sent, set([doc]), doc.origin)
        sentences = set(sent2sent.values())
        return docs, sentences

    def process(self, htmls):
        return self.clean(htmls)



class JavaDocCleaner(BaseCleaner):
    __name__ = "Javadoc Cleaner"

    def __init__(self, **cfg):
        super(self.__class__, self).__init__(**cfg)

    def worker(self, html):
        origin, html_path, html_text = html
        soup = BeautifulSoup(html_text, "lxml")
        strings = []
        for div in soup.select(".block"):
            string = div.get_text().strip()
            if len(string) > 0 and string[-1] not in set(".?!"):
                string = string + "."
            strings.append(string)
        doc = Doc(" ".join(strings), {html_path})
        return doc


if __name__ == "__main__":
    html_cleaner = HTMLCleaner()
    rs = html_cleaner.process(['''<!DOCTYPE html>
<html lang="en">
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<title>

  Quickstart for Deeplearningj | Deeplearning4j

</title>
<link href="/css/plugins/plugins.css" rel="stylesheet">
<link href="/css/style.css" rel="stylesheet">
<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.1.0/css/all.css" integrity="sha384-lKuwvrZot6UHsBSfcMvOkWwlCMgc0TaWr+30HWe3a4ltaBwTZhyTEggF5tJv8tbt" crossorigin="anonymous">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-light navbar-color nav-sticky-top">
<div class="search-inline">
<form>
<input type="text" class="form-control" placeholder="Type and hit enter...">
<button type="submit"><i class="ti-search"></i></button>
<a href="javascript:void(0)" class="search-close"><i class="ti-close"></i></a>
</form>
</div>
<div class="container">
<button class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse" data-target="#navbarNavDropdown" aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
<span class="navbar-toggler-icon"></span>
</button>
<a class="navbar-brand" href="/"><img src="/images/logo.png" alt="Deeplearning4j"></a>
<div id="navbarNavDropdown" class="navbar-collapse collapse">
<ul class="navbar-nav ml-auto">
<li class="nav-item nav-button nav-cta">
<a class="nav-item btn btn-rounded btn-outline-warning" href="/docs/latest/deeplearning4j-quickstart">Quickstart</a>
</li>
<li class="nav-item">
<a class="nav-link dropdown-none" href="/docs/latest/">Guide</a>
</li>
<li class="nav-item">
<a class="nav-link dropdown-none" href="/api/latest/" target="_blank">API</a>
</li>
<li class="nav-item">
<a class="nav-link dropdown-none" href="https://github.com/deeplearning4j/dl4j-examples" target="_blank">Examples</a>
</li>
<li class="nav-item">
<a class="nav-link dropdown-none" href="/tutorials/setup">Tutorials</a>
</li>
<li class="nav-item">
<a class="nav-link dropdown-none" href="/support">Support</a>
</li>
<li class="nav-item">
<a class="nav-link dropdown-none" href="/release-notes">1.0.0-beta2</a>
</li>
</ul>
</div>
<div class="navbar-right-elements">
<ul class="list-inline">

<li class="list-inline-item">
<a href="https://gitter.im/deeplearning4j/deeplearning4j" target="_blank" class="gitter-btn" data-toggle="tooltip" data-original-title="Chat with us"><i class="fab fa-gitter"></i></a>
</li>
<li class="list-inline-item">
<a href="https://github.com/deeplearning4j/deeplearning4j" target="_blank" class="gitter-btn"><i class="fab fa-github"></i></a>
</li>
</ul>
</div>
</div>
</nav>
<div class="page-titles title-dark pt30 pb20 mb50">
<div class="container">
<div class="row">
<div class=" col-md-6">
<h4><span>Quickstart for Deeplearningj</span></h4>
</div>
<div class="col-md-6 mb0">
<ol class="breadcrumb text-md-right">
<li class="breadcrumb-item"><a href="./setup">Tutorials</a></li>
</ol>
 </div>
</div>
</div>
</div>
<div class="container mb70">
<div class="row">
<div class="col-lg-3 pt10 mb40">
<div class="mb40">
<ul class="list-unstyled categories guide-categories">
<li>
<h4><button class="no-btn category" type="button" data-toggle="collapse" data-target="#Tutorialscollapse" aria-controls="Tutorialscollapse" aria-expanded="true">
Tutorials
</button></h4>
<ul class="list-unstyled collapse show" id="Tutorialscollapse">
<li><a href="/tutorials/00-quickstart-for-deeplearning4j">
Quickstart for Deeplearningj <i class="fa fa-caret-right"></i>
</a></li>
<li><a href="/tutorials/01-multilayernetwork-and-computationgraph">
MultiLayerNetwork and ComputationGraph
</a></li>
<li><a href="/tutorials/02-built-in-data-iterators">
Built-in Data Iterators
</a></li>
<li><a href="/tutorials/03-logistic-regression">
Logistic Regression
</a></li>
<li><a href="/tutorials/04-feed-forward">
Feed-forward
</a></li>
<li><a href="/tutorials/05-basic-autoencoder-anomaly-detection-using-reconstruction-error">
Basic Autoencoder- Anomaly Detection Using Reconstruction Error
</a></li>
<li><a href="/tutorials/06-advanced-autoencoder-trajectory-clustering-using-ais">
Advanced Autoencoder- Trajectory Clustering using AIS
</a></li>
<li><a href="/tutorials/07-convolutions-train-facenet-using-center-loss">
Convolutions- Train FaceNet Using Center Loss
</a></li>
<li><a href="/tutorials/08-rnns-sequence-classification-of-synthetic-control-data">
RNNs- Sequence Classification of Synthetic Control Data
</a></li>
<li><a href="/tutorials/09-early-stopping">
Early Stopping
</a></li>
<li><a href="/tutorials/10-layers-and-preprocessors">
Layers and Preprocessors
</a></li>
<li><a href="/tutorials/11-hyperparameter-optimization">
Hyperparameter Optimization
</a></li>
<li><a href="/tutorials/12-clinical-time-series-lstm-example">
 Clinical Time Series LSTM Example
</a></li>
<li><a href="/tutorials/13-clinical-lstm-time-series-example-using-skil">
Clinical LSTM Time Series Example Using SKIL
</a></li>
<li><a href="/tutorials/14-parallel-training">
Parallel Training
</a></li>
<li><a href="/tutorials/15-sea-temperature-convolutional-lstm-example">
Sea Temperature Convolutional LSTM Example
</a></li>
<li><a href="/tutorials/16-sea-temperature-convolutional-lstm-example-2">
Sea Temperature Convolutional LSTM Example
</a></li>
<li><a href="/tutorials/17-instacart-multitask-example">
Instacart Multitask Example
</a></li>
<li><a href="/tutorials/18-instacart-single-task-example">
Instacart Single Task Example
</a></li>
<li><a href="/tutorials/19-cloud-detection-example">
Cloud Detection Example
</a></li>
</ul>
</li>
<li>
<h4><button class="no-btn category" type="button" data-toggle="collapse" data-target="#Setupcollapse" aria-controls="Setupcollapse" aria-expanded="true">
Setup
</button></h4>
<ul class="list-unstyled collapse show" id="Setupcollapse">
<li><a href="/tutorials/setup">
Prerequisites
</a></li>
</ul>
</li>
</ul>
</div>
</div>
<div class="col-lg-9 page-content">
<center><a href="https://raw.githubusercontent.com/deeplearning4j/dl4j-examples/master/tutorials/00.%20Quickstart%20for%20Deeplearning4j.json" target="_blank" class="btn btn-warning btn-rounded mb40" role="button">Download this notebook</a></center>
<h1 id="quickstart-for-deeplearning4j">Quickstart for Deeplearning4j</h1>
<p>Deeplearning4j - also known as “DL4J” - is a
high performance domain-specific language to configure deep neural networks,
which are made of multiple layers. Deeplearning4j is <a href="https://github.com/deeplearning4j/deeplearning4j/">open
source</a>, written in C++,
Java, Scala, and Python, and maintained by the Eclipse Foundation &amp; community
contributors.</p>
<h3 id="before-you-get-started">Before you get started</h3>
<p>If you are having difficulty, we
recommend you join our <a href="https://gitter.im/deeplearning4j/deeplearning4j">Gitter
chat</a>. Gitter is a community
where you can request help and give feedback, but please do use this guide
before asking questions we’ve answered below. If you are new to deep learning,
we’ve included a <a href="https://deeplearning4j.org/deeplearningforbeginners.html">road map for
beginners</a> with links
to courses, readings and other resources. For a longer and more detailed version
of this guide, please visiting the Deeplearning4j <a href="https://deeplearning4j.org/gettingstarted">Getting
Started</a> guide.</p>
<h2 id="handwriting-classification">Handwriting classification</h2>
<p><img src="data:image/png;base64,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" style="float: right; display: inline-block; margin-left: 12px; margin-bottom: 12px" /></p>
<p>In this quickstart, you will create a deep neural
network using Deeplearning4j and train a model capable of classifying random
handwriting digits. While handwriting recognition has been attempted by
different machine learning algorithms over the years, deep learning performs
remarkably well and achieves an accuracy of over 99.7% on the
<a href="https://en.wikipedia.org/wiki/MNIST_database">MNIST</a> dataset. For this
tutorial, we will classify digits in <a href="https://www.nist.gov/itl/iad
/image-group/emnist-dataset">EMNIST</a>, the “next generation” of MNIST and a larger
dataset.</p>
<p>This tutorial is written in Scala, a Java-based language that is well
suited for notebooks like this one.</p>
<h3 id="what-you-will-learn">What you will learn</h3>
<ol>
<li>Load a dataset
for a neural network.</li>
<li>Format EMNIST for image recognition.</li>
<li>Create a deep
neural network.</li>
<li>Train a model.</li>
<li>Evaluate the performance of your model.</li>
</ol>
<h3 id="prepare-your-workspace">Prepare your workspace</h3>
<p>Notebooks rely on an interpreter to execute the code
inside of them. This notebook uses two different interpreters,
<a href="https://zeppelin.apache.org/docs/0.7.1/interpreter/markdown.html">Markdown</a> and
<a href="https://zeppelin.apache.org/docs/0.7.1/interpreter/spark.html">Spark</a>. All of
the text you’ve seen so far uses Markdown (and if you view the source code for
the paragraph you’ll see it starts with <code class="highlighter-rouge">%md</code> which calls for that paragraph to
be executed by Markdown). Because the Spark interpreter is the default, the code
you will see below does not explicity call for <code class="highlighter-rouge">%spark</code>.</p>
<p>Like most programming
languages, you need to explicitly import the classes you want to use into scope.
Below, we will import common Deeplearning4j classes that will help us configure
and train a neural network. The code below is written in Scala.</p>
<p>Note we import
methods from Scala’s <code class="highlighter-rouge">JavaConversions</code> class because this will allow us to use
native Scala collections while maintaining compatibility with Deeplearning4j’s
Java collections.</p>
<div class="language-java highlighter-rouge"><div class="highlight"><pre class="highlight"><code><span class="kn">import</span> <span class="nn">scala.collection.JavaConversions._</span>

<span class="kn">import</span> <span class="nn">org.deeplearning4j.datasets.iterator._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.datasets.iterator.impl._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.api._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.multilayer._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.graph._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.conf._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.conf.inputs._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.conf.layers._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.nn.weights._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.optimize.listeners._</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.datasets.datavec.RecordReaderMultiDataSetIterator</span>
<span class="kn">import</span> <span class="nn">org.deeplearning4j.eval.Evaluation</span>

<span class="kn">import</span> <span class="nn">org.nd4j.linalg.learning.config._</span> <span class="c1">// for different updaters like Adam, Nesterovs, etc.</span>
<span class="kn">import</span> <span class="nn">org.nd4j.linalg.activations.Activation</span> <span class="c1">// defines different activation functions like RELU, SOFTMAX, etc.</span>
<span class="kn">import</span> <span class="nn">org.nd4j.linalg.lossfunctions.LossFunctions</span> <span class="c1">// mean squared error, multiclass cross entropy, etc.</span>
</code></pre></div></div>
<h3 id="prepare-data-for-loading">Prepare data for loading</h3>
<p>Dataset iterators are important pieces of code
that help batch and iterate across your dataset for training and inferring with
neural networks. Deeplearning4j comes with a built-in implementation of a
<code class="highlighter-rouge">BaseDatasetIterator</code> for EMNIST known as <code class="highlighter-rouge">EmnistDataSetIterator</code>. This
particular iterator is a convenience utility that handles downloading and
preparation of data.</p>
<p>Note that we create two different iterators below, one for
training data and the other for for evaluating the accuracy of our model after
training. The last <code class="highlighter-rouge">boolean</code> parameter in the constructor indicates whether we
are instantiating test/train.</p>
<p>You won’t need it for this tutorial, you can
learn more about loading data for neural networks in this <a href="https://deeplearning4j.org/etl-userguide">ETL user
guide</a>. DL4J comes with many record
readers that can load and convert data into ND-Arrays from CSVs, images, videos,
audio, and sequences.</p>
<div class="language-java highlighter-rouge"><div class="highlight"><pre class="highlight"><code><span class="kn">import</span> <span class="nn">org.deeplearning4j.datasets.iterator.impl.EmnistDataSetIterator</span>

<span class="n">val</span> <span class="n">batchSize</span> <span class="o">=</span> <span class="mi">16</span> <span class="c1">// how many examples to simultaneously train in the network</span>
<span class="n">val</span> <span class="n">emnistSet</span> <span class="o">=</span> <span class="n">EmnistDataSetIterator</span><span class="o">.</span><span class="na">Set</span><span class="o">.</span><span class="na">BALANCED</span>
<span class="n">val</span> <span class="n">emnistTrain</span> <span class="o">=</span> <span class="k">new</span> <span class="n">EmnistDataSetIterator</span><span class="o">(</span><span class="n">emnistSet</span><span class="o">,</span> <span class="n">batchSize</span><span class="o">,</span> <span class="kc">true</span><span class="o">)</span>
<span class="n">val</span> <span class="n">emnistTest</span> <span class="o">=</span> <span class="k">new</span> <span class="n">EmnistDataSetIterator</span><span class="o">(</span><span class="n">emnistSet</span><span class="o">,</span> <span class="n">batchSize</span><span class="o">,</span> <span class="kc">false</span><span class="o">)</span>
</code></pre></div></div>
<h2 id="build-the-neural-network">Build the neural network</h2>
<p>For any neural network you build in Deeplearning4j,
the foundation is the <code class="highlighter-rouge">NeuralNetConfiguration</code>
<a href="https://deeplearning4j.org/neuralnet-configuration.html">class</a>. This is where
you configure hyperparameters, the quantities that define the architecture and
how the algorithm learns. Intuitively, each hyperparameter is like one
ingredient in a meal, a meal that can go very right, or very wrong… Luckily,
you can adjust hyperparameters if they don’t produce the right results.</p>
<p>The
<code class="highlighter-rouge">list()</code> method specifies the number of layers in the net; this function
replicates your configuration n times and builds a layerwise configuration.</p>
<p>###
So what exactly is the hidden layer?</p>
<p><img src="data:image/png;base64,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" alt="hidden layers" style="float: right; display: inline-block; margin-left: 12px; margin-top: 12px" /></p>
<p>Each node (the circles) in the hidden layer represents
a feature of a handwritten digit in the MNIST dataset. For example, imagine you
are looking at the number 6. One node may represent rounded edges, another node
may represent the intersection of curly lines, and so on and so forth. Such
features are weighted by importance by the model’s coefficients, and recombined
in each hidden layer to help predict whether the handwritten number is indeed 6.
The more layers of nodes you have, the more complexity and nuance they can
capture to make better predictions.</p>
<p>You could think of a layer as “hidden”
because, while you can see the input entering a net, and the decisions coming
out, it’s difficult for humans to decipher how and why a neural net processes
data on the inside. The parameters of a neural net model are simply long vectors
of numbers, readable by machines.</p>
<div class="language-java highlighter-rouge"><div class="highlight"><pre class="highlight"><code><span class="n">val</span> <span class="n">outputNum</span> <span class="o">=</span> <span class="n">EmnistDataSetIterator</span><span class="o">.</span><span class="na">numLabels</span><span class="o">(</span><span class="n">emnistSet</span><span class="o">)</span> <span class="c1">// total output classes</span>
<span class="n">val</span> <span class="n">rngSeed</span> <span class="o">=</span> <span class="mi">123</span> <span class="c1">// integer for reproducability of a random number generator</span>
<span class="n">val</span> <span class="n">numRows</span> <span class="o">=</span> <span class="mi">28</span> <span class="c1">// number of "pixel rows" in an mnist digit</span>
<span class="n">val</span> <span class="n">numColumns</span> <span class="o">=</span> <span class="mi">28</span>

<span class="n">val</span> <span class="n">conf</span> <span class="o">=</span> <span class="k">new</span> <span class="n">NeuralNetConfiguration</span><span class="o">.</span><span class="na">Builder</span><span class="o">()</span>
            <span class="o">.</span><span class="na">seed</span><span class="o">(</span><span class="n">rngSeed</span><span class="o">)</span>
            <span class="o">.</span><span class="na">optimizationAlgo</span><span class="o">(</span><span class="n">OptimizationAlgorithm</span><span class="o">.</span><span class="na">STOCHASTIC_GRADIENT_DESCENT</span><span class="o">)</span>
            <span class="o">.</span><span class="na">updater</span><span class="o">(</span><span class="k">new</span> <span class="n">Adam</span><span class="o">())</span>
            <span class="o">.</span><span class="na">l2</span><span class="o">(</span><span class="mi">1</span><span class="n">e</span><span class="o">-</span><span class="mi">4</span><span class="o">)</span>
            <span class="o">.</span><span class="na">list</span><span class="o">()</span>
            <span class="o">.</span><span class="na">layer</span><span class="o">(</span><span class="k">new</span> <span class="n">DenseLayer</span><span class="o">.</span><span class="na">Builder</span><span class="o">()</span>
                <span class="o">.</span><span class="na">nIn</span><span class="o">(</span><span class="n">numRows</span> <span class="o">*</span> <span class="n">numColumns</span><span class="o">)</span> <span class="c1">// Number of input datapoints.</span>
                <span class="o">.</span><span class="na">nOut</span><span class="o">(</span><span class="mi">1000</span><span class="o">)</span> <span class="c1">// Number of output datapoints.</span>
                <span class="o">.</span><span class="na">activation</span><span class="o">(</span><span class="n">Activation</span><span class="o">.</span><span class="na">RELU</span><span class="o">)</span> <span class="c1">// Activation function.</span>
                <span class="o">.</span><span class="na">weightInit</span><span class="o">(</span><span class="n">WeightInit</span><span class="o">.</span><span class="na">XAVIER</span><span class="o">)</span> <span class="c1">// Weight initialization.</span>
                <span class="o">.</span><span class="na">build</span><span class="o">())</span>
            <span class="o">.</span><span class="na">layer</span><span class="o">(</span><span class="k">new</span> <span class="n">OutputLayer</span><span class="o">.</span><span class="na">Builder</span><span class="o">(</span><span class="n">LossFunctions</span><span class="o">.</span><span class="na">LossFunction</span><span class="o">.</span><span class="na">NEGATIVELOGLIKELIHOOD</span><span class="o">)</span>
                <span class="o">.</span><span class="na">nIn</span><span class="o">(</span><span class="mi">1000</span><span class="o">)</span>
                <span class="o">.</span><span class="na">nOut</span><span class="o">(</span><span class="n">outputNum</span><span class="o">)</span>
                <span class="o">.</span><span class="na">activation</span><span class="o">(</span><span class="n">Activation</span><span class="o">.</span><span class="na">SOFTMAX</span><span class="o">)</span>
                <span class="o">.</span><span class="na">weightInit</span><span class="o">(</span><span class="n">WeightInit</span><span class="o">.</span><span class="na">XAVIER</span><span class="o">)</span>
                <span class="o">.</span><span class="na">build</span><span class="o">())</span>
            <span class="o">.</span><span class="na">pretrain</span><span class="o">(</span><span class="kc">false</span><span class="o">).</span><span class="na">backprop</span><span class="o">(</span><span class="kc">true</span><span class="o">)</span>
            <span class="o">.</spgit an><span class="na">build</span><span class="o">()</span>
</code></pre></div></div>
<h3 id="train-the-model">Train the model</h3>
<p>Now that we’ve built a <code class="highlighter-rouge">NeuralNetConfiguration</code>, we can use
the configuration to instantiate a <code class="highlighter-rouge">MultiLayerNetwork</code>. When we call the
<code class="highlighter-rouge">init()</code> method on the network, it applies the chosen weight initialization
across the network and allows us to pass data to train. If we want to see the
loss score during training, we can also pass a listener to the network.</p>
<p>An
instantiated model has a <code class="highlighter-rouge">fit()</code> method that accepts a dataset iterator (an
iterator that extends <code class="highlighter-rouge">BaseDatasetIterator</code>), a single <code class="highlighter-rouge">DataSet</code>, or an ND-Array
(an implementation of <code class="highlighter-rouge">INDArray</code>). Since our EMNIST iterator already extends the
iterator base class, we can pass it directly to fit. If we want to train for
multiple epochs, DL4J also provides a <code class="highlighter-rouge">MultipleEpochsIterator</code> class that can
handle multiple epochs for us.</p>
<div class="language-java highlighter-rouge"><div class="highlight"><pre class="highlight"><code><span class="c1">// create the MLN</span>
<span class="n">val</span> <span class="n">network</span> <span class="o">=</span> <span class="k">new</span> <span class="n">MultiLayerNetwork</span><span class="o">(</span><span class="n">conf</span><span class="o">)</span>
<span class="n">network</span><span class="o">.</span><span class="na">init</span><span class="o">()</span>

<span class="c1">// pass a training listener that reports score every 10 iterations</span>
<span class="n">val</span> <span class="n">eachIterations</span> <span class="o">=</span> <span class="mi">5</span>
<span class="n">network</span><span class="o">.</span><span class="na">addListeners</span><span class="o">(</span><span class="k">new</span> <span class="n">ScoreIterationListener</span><span class="o">(</span><span class="n">eachIterations</span><span class="o">))</span>

<span class="c1">// fit a dataset for a single epoch</span>
<span class="c1">// network.fit(emnistTrain)</span>

<span class="c1">// fit for multiple epochs</span>
<span class="c1">// val numEpochs = 2</span>
<span class="c1">// network.fit(new MultipleEpochsIterator(numEpochs, emnistTrain))</span>
</code></pre></div></div>
<h3 id="evaluate-the-model">Evaluate the model</h3>
<p>Deeplearning4j exposes several tools to <a href="https://deeplearning4j.org/evaluation">evaluate the
performance</a> of a model. You can perform
basic evaluation and get metrics such as precision and accuracy, or use a
Receiver Operating Characteristic (ROC). Note that the general <code class="highlighter-rouge">ROC</code> class works
for binary classifiers, whereas <code class="highlighter-rouge">ROCMultiClass</code> is meant for classifiers such as
the model we are building here.</p>
<p>A <code class="highlighter-rouge">MultiLayerNetwork</code> conveniently has a few
methods built-in to help us perform evaluation. You can pass a dataset iterator
with your testing/validation data to an <code class="highlighter-rouge">evaluate()</code> method.</p>
<div class="language-java highlighter-rouge"><div class="highlight"><pre class="highlight"><code><span class="c1">// evaluate basic performance</span>
<span class="n">val</span> <span class="n">eval</span> <span class="o">=</span> <span class="n">network</span><span class="o">.</span><span class="na">evaluate</span><span class="o">(</span><span class="n">emnistTest</span><span class="o">)</span>
<span class="n">eval</span><span class="o">.</span><span class="na">accuracy</span><span class="o">()</span>
<span class="n">eval</span><span class="o">.</span><span class="na">precision</span><span class="o">()</span>
<span class="n">eval</span><span class="o">.</span><span class="na">recall</span><span class="o">()</span>

<span class="c1">// evaluate ROC and calculate the Area Under Curve</span>
<span class="n">val</span> <span class="n">roc</span> <span class="o">=</span> <span class="n">network</span><span class="o">.</span><span class="na">evaluateROCMultiClass</span><span class="o">(</span><span class="n">emnistTest</span><span class="o">)</span>
<span class="n">roc</span><span class="o">.</span><span class="na">calculateAverageAUC</span><span class="o">()</span>

<span class="n">val</span> <span class="n">classIndex</span> <span class="o">=</span> <span class="mi">0</span>
<span class="n">roc</span><span class="o">.</span><span class="na">calculateAUC</span><span class="o">(</span><span class="n">classIndex</span><span class="o">)</span>

<span class="c1">// optionally, you can print all stats from the evaluations</span>
<span class="n">print</span><span class="o">(</span><span class="n">eval</span><span class="o">.</span><span class="na">stats</span><span class="o">())</span>
<span class="n">print</span><span class="o">(</span><span class="n">roc</span><span class="o">.</span><span class="na">stats</span><span class="o">())</span>
</code></pre></div></div>
<h1 id="whats-next">What’s next</h1>
<p>Now that you’ve learned how to get started and train your first
model, head to the Deeplearning4j website to see <a href="https://deeplearning4j.org/tutorials">all the other
tutorials</a> that await you. Learn how to
build dataset iterators, train a facial recognition network like FaceNet, and
more.</p>
</div>
</div>
</div>
<div class="container mb10 pt30">
<div class="row special-feature">
<div class="col-md-3 col-sm-6 margin20">
<div class="s-feature-box text-center" onclick="window.open('/api/latest/','_blank');">
<div class="mask-top">
 <i class="fa fa-code"></i>
<h4>API Reference</h4>
</div>
<div class="mask-bottom">
<i class="fa fa-code"></i>
<h4>API Reference</h4>
<p>Detailed API docs for all libraries including DL4J, ND4J, DataVec, and Arbiter.</p>
</div>
</div>
</div>
<div class="col-md-3 col-sm-6 margin20">
<div class="s-feature-box text-center" onclick="window.open('https://github.com/deeplearning4j/dl4j-examples','_blank');">
<div class="mask-top">
<i class="fa fa-folder"></i>
<h4>Examples</h4>
</div>
<div class="mask-bottom">
<i class="fa fa-folder"></i>
<h4>Examples</h4>
<p>Explore sample projects and demos for DL4J, ND4J, and DataVec in multiple languages including Java and Kotlin.</p>
</div>
</div>
</div>
<div class="col-md-3 col-sm-6 margin20">
<div class="s-feature-box text-center" onclick="window.open('/tutorials/setup','_blank');">
<div class="mask-top">
<i class="fa fa-file-code"></i>
<h4>Tutorials</h4>
</div>
<div class="mask-bottom">
<i class="fa fa-file-code"></i>
<h4>Tutorials</h4>
<p>Step-by-step tutorials for learning concepts in deep learning while using the DL4J API.</p>
</div>
</div>
</div>
<div class="col-md-3 col-sm-6 margin20">
<div class="s-feature-box text-center" onclick="window.location='/docs/latest/';">
<div class="mask-top">
<i class="fa fa-book"></i>
<h4>Guide</h4>
</div>
<div class="mask-bottom">
<i class="fa fa-book"></i>
<h4>Guide</h4>
<p>In-depth documentation on different scenarios including import, distributed training, early stopping, and GPU setup.</p>
</div>
</div>
</div>
</div>
</div>
<div class="bg-parallax parallax-overlay">
<div class="container pt40 pb40">
<div class="row">
<div class="col-lg-9 pt10">
<h2 class="text-white">
Deploying models? There's a tool for that.
</h2>
</div>
<div class="col-lg-3 pt0">
<a class="btn btn-lg btn-white-outline btn-rounded" href="https://skymind.ai/platform" target="_blank">
Learn More <i class="fa fa-external-link-square-alt"></i>
</a>
</div>
</div>
</div>
</div>
<footer class="footer footer-standard pt50 pb10">
<div class="container">
<div class="row">
<div class="col-lg-4 col-md-6 mb40">
<h3>Eclipse Deeplearning4j</h3>
<p>
Eclipse Deeplearning4j is an open-source, distributed deep-learning project in Java and Scala spearheaded by the people at <a href="https://skymind.ai/" target="_blank">Skymind</a>. DL4J supports GPUs and is compatible with distributed computing software such as Apache Spark and Hadoop.
</p>
<a href="/about" class="btn btn-white-outline btn-sm btn-rounded">Learn More</a>
</div>
<div class="col-lg-2 col-md-6 mb40">
<h3>Quick links</h3>
<ul class="list-unstyled footer-list-item">
<li>
<a href="/about">About</a>
</li>
<li>
<a href="/faq">FAQs</a>
</li>
<li>
<a href="/docs/latest/deeplearning4j-contribute">Contribute</a>
</li>
 <li>
<a href="/press">Press</a>
</li>
<li>
<a href="/why-deep-learning">Why Deep Learning?</a>
</li>
</ul>
</div>
<div class="col-lg-2 col-md-6 mb40">
<h3>&nbsp;</h3>
<ul class="list-unstyled footer-list-item">
<li>
<a href="/api/latest/" target="_blank" g>API</a>
</li>
<li>
<a href="https://github.com/deeplearning4j/dl4j-examples" target="_blank">Examples</a>
</li>
<li>
<a href="/tutorials/setup">Tutorials</a>
</li>
<li>
<a href="/docs/latest/">Guide</a>
</li>
<li>
<a href="/support">Support</a>
</li>
</ul>
</div>
<div class="col-lg-4 col-md-6 mb40">
<h3>Statistics</h3>
<img src="/images/github-stats.png" alt="" class="img-fluid">
</div>
</div>
</div>
</footer>
<div class="footer-bottomAlt">
<div class="container">
<div class="row">
<div class="col-lg-7">
<div class="clearfix">
<a href="https://www.facebook.com/deeplearning4j/" target="_blank" class="social-icon-sm si-dark si-facebook si-dark-round">
<i class="fab fa-facebook"></i>
<i class="fab fa-facebook"></i>
</a>
<a href="https://twitter.com/deeplearning4j" target="_blank" class="social-icon-sm si-dark si-twitter si-dark-round">
<i class="fab fa-twitter"></i>
<i class="fab fa-twitter"></i>
</a>
<a href="https://github.com/deeplearning4j/deeplearning4j/" target="_blank" class="social-icon-sm si-dark si-github si-dark-round">
<i class="fab fa-github"></i>
<i class="fab fa-github"></i>
</a>
</div>
</div>
<div class="col-lg-5">
<span>Copyright &copy; 2018. Skymind. DL4J is licensed Apache 2.0.</span>
</div>
</div>
</div>
</div>

<a href="#" class="back-to-top hidden-xs-down" id="back-to-top"><i class="ti-angle-up"></i></a>

<script src="/js/plugins/plugins.js"></script>
<script src="/js/assan.custom.js"></script>
<script type="text/javascript">
    // get started sort
    var $gs = $('.mason-grid-card:contains("Get Started")'),
        gsCopy = $gs.clone()
    $gs.remove()
    $('.mason-grid').first().prepend(gsCopy)
    // keras sort
    var $ki = $('.mason-grid-card:contains("Keras Import")'),
        kiCopy = $ki.clone()
    $ki.remove()
    $('.mason-grid').last().append(kiCopy)

    $('.mason-grid').masonry({
      // options
      itemSelector: '.mason-grid-card',
      columnWidth: '.mason-grid-card',
      transitionDuration  : 0
    });
</script>

<script>
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');
ga('create', 'UA-48811288-1', 'auto');
ga('require', 'linkid', 'linkid.js');
ga('send', 'pageview');
ga('require', 'displayfeatures');
</script>


<script type="text/javascript">
setTimeout(function(){var a=document.createElement("script");
var b=document.getElementsByTagName("script")[0];
a.src=document.location.protocol+"//script.crazyegg.com/pages/scripts/0025/5605.js?"+Math.floor(new Date().getTime()/3600000);
a.async=true;a.type="text/javascript";b.parentNode.insertBefore(a,b)}, 1);
</script>


<script type="text/javascript" id="hs-script-loader" async defer src="//js.hs-scripts.com/2179705.js"></script>


<script type="text/javascript">
piAId = '457082';
piCId = '66281';
piHostname = 'pi.pardot.com';
(function() {
function async_load(){
    var s = document.createElement('script'); s.type = 'text/javascript';
    s.src = ('https:' == document.location.protocol ? 'https://pi' : 'http://cdn') + '.pardot.com/pd.js';
    var c = document.getElementsByTagName('script')[0]; c.parentNode.insertBefore(s, c);
}
if(window.attachEvent) { window.attachEvent('onload', async_load); }
else { window.addEventListener('load', async_load, false); }
})();
</script>


<script src="https://cdn.optimizely.com/js/2296590312.js"></script>

<script type="text/javascript">
            $(function() {
                $('.page-content').flowtype({
                    minFont : 12,
                    maxFont : 18
                });
            })
        </script>
</body>
</html>'''])
    print(rs)
