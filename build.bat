rmdir .\build /s /q
rmdir .\dist /s /q
rmdir .\raspend.egg-info /s /q

python -m pip install --user --upgrade setuptools wheel
python setup.py sdist bdist_wheel