installPath='/opt'
probeSource='/opt/virtualenv'
if [ ! -x "$probeSource" ] ; then
pipInstallVenv=`pip install virtualenv`
case "$pipInstallVenv"
        in
        *already* ) echo "already installed virtualenv.";;
        *Successfully* ) echo "pip install virtualenv success.";;
        * ) echo "this mechine can't install virtualenv,please check your network,or pip is not installed";
	exit;;
esac
installVirtualEnv=`virtualenv --no-site-packages virtualenv`
case "$installVirtualEnv"
        in
        *done*) echo "install new virtual environment success.";;
        *) echo "some error occur when install virtualenv";
        exit;;
esac

cd $probeSource
git clone https://github.com/zoushidong/softprobe.git
source bin/activate
cd softprobe
pip install -r requirement.txt
deactivate
fi
cd $probeSource
source bin/activate
cd softprobe
ps -ef | grep 'python softprobe.py' | awk '{print $2}' | xargs kill -9
nohup python softprobe.py &
deactivate

