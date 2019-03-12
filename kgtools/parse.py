#!/usr/data/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from domainterm.util.saver import Saver
import json


class DataParser:
    def __init__(self, dir):
        self.dir = dir

    def parse_preprocessor(self):
        print("Parsing preprocessor...")
        # try:
        data = Saver.from_disk(str(Path(self.dir, "preprocessor.data")))
        # except Exception:
        #     return
        with Path(self.dir, "sentences_origin.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([str(t) + "\n" + str(t.origin) for t in data["sentences"]]))
        with Path(self.dir, "sentences.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([str(t) for t in data["sentences"]]))
        with Path(self.dir, "code_elements.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([str(t) + "\t" + str(t.uncamel_case) for t in data["code_meta"]["elements"]]))
        with Path(self.dir, "code_relations.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([str(t) for t in data["code_meta"]["relations"]]))

    def parse_tokenizer(self):
        print("Parsing tokenizer...")
        try:
            data = Saver.from_disk(str(Path(self.dir, "tokenizer.data")))
        except Exception:
            return
        with Path(self.dir, "tokenized_sentences.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([sent.tokenized_text() + "\n" + " ".join([t.lemma for t in sent.token_seq]) + "\n" + " ".join([t.pos for t in sent.token_seq]) + "\n" + " ".join([t.dep for t in sent.token_seq]) + "\n" + " ".join([np.text for np in sent.noun_chunks]) for sent in data["sentences"]]))
        with Path(self.dir, "vocab.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([w for w in data["vocab"].words]))

    def parse_extractor(self):
        print("Parsing extractor...")
        try:
            data = Saver.from_disk(str(Path(self.dir, "extractor.data")))
        except Exception:
            return
        with Path(self.dir, "concept-seeds.txt").open("w", encoding="utf-8") as f:
            concept_seeds = [c.text for c in data["seeds"]]
            f.write("\n".join(list(sorted(concept_seeds, key=lambda x: x))))

        with Path(self.dir, "seed_vote.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(list(sorted([str(ele) for ele in data["seed_vote"]], key=lambda x: x))))
        
        with Path(self.dir, "seed_freq.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(list(sorted([str(ele) for ele in data["seed_freq"]], key=lambda x: x))))

        with Path(self.dir, "labeled.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(["{}\n{}".format(sent.tokenized_text(), sent.tag_seq()) for sent in data["sentences"]]))

    def parse_recognizer(self):
        print("Parsing recognizer...")
        try:
            data = Saver.from_disk(str(Path(self.dir, "recognizer.data")))
        except Exception:
            return
        Path(self.dir, "steps").mkdir(parents=True, exist_ok=True)
        for i, step in enumerate(data["recognize_steps"]):
            with Path(self.dir, "steps/concepts{}.txt".format(i)).open("w", encoding="utf-8") as f:
                f.write("\n".join(list(sorted([c.text for c in step[0]], key=lambda x: x))))

            with Path(self.dir, "steps/vote{}.txt".format(i)).open("w", encoding="utf-8") as f:
                f.write("\n".join([str(ele) for ele in step[1]]))

        with Path(self.dir, "concepts.txt").open("w", encoding="utf-8") as f:
            concepts = [c.text for c in data["concepts"]]
            f.write("\n".join(list(sorted(concepts, key=lambda x: x))))

        with Path(self.dir, "concept_vote.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(list(sorted([str(ele) for ele in data["concept_vote"]], key=lambda x: x))))
        
        with Path(self.dir, "concept_freq.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(list(sorted([str(ele) for ele in data["concept_freq"]], key=lambda x: x))))


        concept_sents = {}
        for sent in data["sentences"]:
            for concept in sent.concepts:
                if concept.text not in concept_sents:
                    concept_sents[concept.text] = []
                concept_sents[concept.text].append(sent.text)
        with Path(self.dir, "concept_sents.json").open("w", encoding="utf-8") as f:
            json.dump(concept_sents, f, indent=4)

    def parse_fusion(self):
        print("Parsing fusion...")
        try:
            data = Saver.from_disk(str(Path(self.dir, "fusion.data")))
        except Exception:
            return
        synsets = data["synsets"]
        with Path(self.dir, "synsets.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(list(sorted([c.text for c in synsets], key=lambda x: x))))
        # with Path("output/dl4j/result4/abbrs.json").open("w", encoding="utf-8") as f:
        #     json.dump(abbrs, f, indent=4)
            # f.write("\n".join([str(t) for t in abbrs]))

    def parse_builder(self):
        print("Parsing buidler...")
        try:
            data = Saver.from_disk(str(Path(self.dir, "builder.data")))
        except Exception:
            return

        with Path(self.dir, "concepts.txt").open("w", encoding="utf-8") as f:
            concepts = [c.text for c in data["concepts"]]
            f.write("\n".join(list(sorted(concepts, key=lambda x: x))))

        with Path(self.dir, "synsets.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join(list(sorted([c.text for c in data["synsets"]], key=lambda x: x))))        

        relations = data["relations"]
        with Path(self.dir, "relatoins.txt").open("w", encoding="utf-8") as f:
            f.write("\n".join([str(r) for r in relations]))
        relation_dict = []
        for r in relations:
            relation_dict.append({
                "start_concepts": str(r.start).strip("<>").split(", "),
                "end_concepts": str(r.end).strip("<>").split(", "),
                "type": str(r.type).replace("RelationType.", "")
            })
        with Path(self.dir, "relatoins.json").open("w", encoding="utf-8") as f:
            json.dump(relation_dict, f, indent=4)

    def parse_selector(self):
        print("Parsing selector...")
        try:
            data = Saver.from_disk(str(Path(self.dir, "selector.data")))
        except Exception:
            return

        with Path(self.dir, "selected_sentences.json").open("w", encoding="utf-8") as f:
            d = {str(synset): [str(s) for s, _ in sents] for synset, sents in data["selected_sentences"]}
            json.dump(d, f, indent=4)

    # def parse_packages(self):
    #     data = Saver.from_disk("output/dl4j/result4/preprocessor.data")
    #     print(data["code"]["packages"])
    #     with Path(self.dir, "output/dl4j/result4/packages.txt").open("w", encoding="utf-8") as f:
    #         f.write("\n".join(list(sorted(data["code"]["packages"], key=lambda x: x))))

    def parse_all(self):
        # print(self.data.keys())
        self.parse_preprocessor()
        self.parse_tokenizer()
        self.parse_extractor()
        self.parse_recognizer()
        self.parse_fusion()
        self.parse_builder()
        self.parse_selector()

    def parse_by_name(self, name):
        if "preprocessor" == name:
            self.parse_preprocessor()
        elif "tokenizer" == name:
            self.parse_tokenizer()
        elif "extractor" == name:
            self.parse_extractor()
        elif "recognizer" == name:
            self.parse_recognizer()
        elif "fusion" == name:
            self.parse_fusion()
        elif "builder" == name:
            self.parse_builder()
        elif "selector" == name:
            self.parse_selector()



if __name__ == "__main__":
    import sys
    assert len(sys.argv) > 1
    print(sys.argv[1])
    dataParser = DataParser(sys.argv[1])
    # dataParser.parse_preprocessor()
    # dataParser.parse_tokenizer()
    dataParser.parse_selector()
