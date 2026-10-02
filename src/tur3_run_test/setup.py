from setuptools import find_packages, setup
from glob import glob
package_name = 'tur3_run_test'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name+"/launch", glob('launch/*.launch.py')),
        ('share/' + package_name+"/config", glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fzx',
    maintainer_email='2835320841@qq.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'run_slope=tur3_run_test.run_slope:main',
            'test=tur3_run_test.test:main',
            'keyboard_control=tur3_run_test.keyboard_control:main',
            'nav_to_pose=tur3_run_test.nav_to_pose:main',
        ],
    },
)
