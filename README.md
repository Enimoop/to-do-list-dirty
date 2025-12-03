# to-do-list app
To-Do-List application built with django to Create, Update and Delete tasks.
<br>
<br>
![todolist](https://user-images.githubusercontent.com/65074901/125083144-a5e03900-e0e5-11eb-9092-da716a30a5f3.JPG)

## Versioning and commit management
### Commit naming convention
This naming convention is inspired by : https://www.conventionalcommits.org/en/v1.0.0/

The type used in this project are : 
- feat – for adding a new feature

- fix – for correcting a bug

- refactor – for improving the code without changing behavior

- chore – for maintenance or version bumps

- docs – for documentation updates

- style – for formatting (no code change)

Example : 
```
style: added new css for update button
``` 

### Semantic Version
We follow the Semantic Version rules : https://semver.org/

A version number has the format:

```
MAJOR.MINOR.PATCH
```

Meaning:

- MAJOR – increased when breaking changes are introduced

- MINOR – increased when a new feature is added without breaking anything

- PATCH – increased when bugs are fixed

Example:
1.0.1 means major version 1, no new features, and one patch.

### Automated Version Update

A build script (build.sh) is used to:

- take a version number as input

- update the version inside the project

- tag the current commit with this version

- generate a release archive (ZIP file)