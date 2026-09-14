"""Fit-scoped text transforms and symmetric existing-embedding comparisons."""
import hashlib
import re
import numpy as np

from screening2_common import *
from screening_ablation import fit_vocabulary
from stage2 import pair_features,validate_embedding,jaccard


def identifiers(text):
    # ASCII codes and hyphenated words are explicit clues, never hard constraints.
    tokens=re.findall(r"(?<![A-Za-z0-9])[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*(?![A-Za-z0-9])",text)
    return {v for v in tokens if re.search(r"[A-Za-z]",v) and (re.search(r"\d",v) or "-" in v)}


def identifier_features(a,b):
    x,y=identifiers(a),identifiers(b)
    return [jaccard(x,y),float(bool(x) and bool(y) and not x&y),float(not x or not y),float(not x and not y)]


def matrix_key(ids):
    return hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()[:16]


def source_data(include_development=False):
    splits=("train","development") if include_development else ("train",)
    libraries=[lib for split in splits for lib in load_split(split)[0]["libraries"]]
    items={item["id"]:item for lib in libraries for item in lib["items"]}
    embeddings={key:read(BASELINE/"embeddings"/f"{key}.json") for key in items}
    for key,item in items.items():validate_embedding(item,embeddings[key])
    return libraries,items,embeddings


def features(run,fit_ids,include_development=False):
    require(not any(int(v[2:])>18 for v in fit_ids),"development cannot fit features")
    if include_development: require((run/"selection.json").exists(),"development confirmation requires frozen screen selection")
    name=matrix_key(fit_ids)+("-confirmation" if include_development else "")
    path=run/"features"/f"{name}.json"
    if path.exists():return read(path)
    boundary(run,"features:"+name,planned=10*1024**2)
    libraries,items,embeddings=source_data(include_development)
    vectorizer,vocabulary=fit_vocabulary(libraries,fit_ids)
    truth=gold("train")+(gold("development") if include_development else [])
    result=[]
    for lib in libraries:
        ids=[i["id"] for i in lib["items"]];index={key:i for i,key in enumerate(ids)}
        mat=vectorizer.transform([items[key]["text"] for key in ids]);lexical=(mat@mat.T).toarray()
        for row in [r for r in truth if r["library"]==lib["id"]]:
            a,b=row["first"],row["second"]
            values=pair_features(items[a],items[b],embeddings[a],embeddings[b],lexical[index[a],index[b]])
            values+=identifier_features(items[a]["text"],items[b]["text"])
            require(all(v is not None and np.isfinite(v) for v in values),"missing feature; stop instead of imputing silently")
            result.append(row|{"features":values})
    value={"fitLibraries":fit_ids,"tfidf":vocabulary,"rows":result,"embeddingSpace":sorted({r["space"] for r in embeddings.values()})}
    save(path,value);return value


def matrix(rows,kind,embeddings=None,extra=None):
    if kind=="six":return np.asarray([r["features"][:6] for r in rows],dtype=np.float64)
    values=np.asarray([r["features"] for r in rows],dtype=np.float64)
    if kind=="expanded":return values
    if kind=="hybrid":
        require(extra is not None,"hybrid scores missing")
        scores=np.clip([extra[r["id"]] for r in rows],1e-6,1-1e-6)
        return np.column_stack((values,np.log(scores/(1-scores))))
    require(kind=="vectors" and embeddings is not None,"invalid feature matrix request")
    vectors=[]
    for row in rows:
        a,b=embeddings[row["first"]],embeddings[row["second"]]
        require(a["space"]==b["space"],"embedding spaces differ")
        components=[]
        for key in ("contextual","sentence"):
            x,y=np.asarray(a[key]),np.asarray(b[key])
            require(x.shape==y.shape==(512,),"embedding dimension changed")
            components.extend((np.abs(x-y),x*y))
        vectors.append(np.concatenate(components))
    return np.column_stack((vectors,values))


def task_id(trial,fit_ids,seed):
    require(re.fullmatch(r"[ABC][123]",trial),"invalid task trial")
    return f"{trial}-seed-{seed}-fit-{matrix_key(fit_ids)}"


def partition(rows,ids):
    return [r for r in rows if r["library"] in ids]
