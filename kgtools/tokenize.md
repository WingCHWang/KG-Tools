### nltk
* "" -> \`\`''
* i.e. -> i.e .
* e.g. -> e.g .
* app:initialExpandedChildrenCount="0" -> app : initialExpandedChildrenCount= '' 0 ''


### spacy
* 连字符会被拆开，如：up-to-date -> up - to - date
* 括号分割有问题，如：onNewIntent(Intent) -> onNewIntent(Intent )
* 尖括号问题，如：<manifest> -> < manifest>
* app:initialExpandedChildrenCount="0" -> app : initialExpandedChildrenCount="0 "