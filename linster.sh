
help_text='
Использование: ./linter.sh [путь] [опции]\n
Путь по умолчанию - папка, в которой расположен linter.sh\n
По умолчанию линтер только показывает возможное улучшение форматирования\n
\n
Опции:\n
  \t-w --write - применить изменения\n
  \t-h --help  - эта справка
'

write=0
path='.'
while [ "$1" != "" ]; do
    case $1 in
        -w | --write)    write=1 ;;
        -h | --help )    echo -e $help_text; exit ;;
         *          )    path=$1;;
    esac
    shift
done

cmd="python -m black ${path}"
if [ $write == 0 ]
then cmd="${cmd} --check --diff"
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
source venv/bin/activate

$cmd