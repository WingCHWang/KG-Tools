if exist sdist (
   echo y | rd /s sdist
)

if exist dist (
   echo y | rd /s dist
)
echo "package project..."
python setup.py sdist
echo "start upload..."
python -m twine upload dist/*.tar.gz