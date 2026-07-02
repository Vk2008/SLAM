import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'slam'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='cs1240328@cse.iitd.ac.in',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'drone_teleop = slam.drone_teleop:main',
            'odom_to_tf_relay = slam.odom_to_tf:main',
            'safety_filter = slam.safety_filter:main',
        ],
    },
)