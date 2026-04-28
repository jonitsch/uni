# Current version of this program. If this includes "-svn", the latter
# will be replaced by "-svn-rX" where "X" is the current SVN revision.
version = "1.0.7"

# SVN revision; this gets automagically updated by SVN on checkout.
svn_rev = "$Rev: 5161 $"

def version_str():
    return version.replace("-svn", "-svn-r%s" % svn_rev[6:-2])
