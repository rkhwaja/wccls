from pathlib import Path

from pytest import fixture

_COLLECT_OPTIONS = ['save', 'test']

def pytest_addoption(parser):
	parser.addoption('--collect', action='store', default='test', help=f'Valid options are {",".join(_COLLECT_OPTIONS)}')

@fixture()
def collect(request):
	value = request.config.getoption('--collect')
	if value not in _COLLECT_OPTIONS:
		raise RuntimeError(f'Invalid value for "collect" option. Options are {",".join(_COLLECT_OPTIONS)}')
	return value

# parameterize tests by the directories under test/filesets
def pytest_generate_tests(metafunc):
	filesetsRoot = Path('tests/filesets')
	if 'fileset' in metafunc.fixturenames:
		allFilesets = [x.name for x in filesetsRoot.iterdir() if x.is_dir()]
		metafunc.parametrize('fileset', allFilesets)
