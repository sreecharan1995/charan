import { isEqual } from 'lodash'
import diffSequences from 'diff-sequences'

/**
 * Compile a JSON Pointer
 * WARNING: this is an incomplete implementation
 * @param {Array.<string | number>} path
 * @return {string}
 */
// use compileJSONPointer from a library instead of defining it again
export function compileJSONPointer (path) {
    return path
        .map(p => ('/' + String(p)
                .replace(/~/g, '~0')
                .replace(/\//g, '~1')
        ))
        .join('')
}

/** @typedef {Array | Object | number | string | boolean | null} JSON */

/** @typedef {'create' | 'update' | 'delete' | 'child-update'} Change */

/**
 * @typedef {Array.<string | number>} Path
 */

/** @typedef {{
 *   change: 'create' | 'update' | 'delete',
 *   pathLeft: Path,
 *   pathRight: Path,
 *   valueLeft?: *,
 *   valueRight?: *
 * }} DiffAction */

/** @typedef {Object<string, Change>} DiffMap */

export const CREATE = 'create'
export const UPDATE = 'update'
export const DELETE = 'delete'
export const CHILD_UPDATE = 'child-update'

/**
 * Compare two JSON objects and return the difference between the left and
 * right object as a map with the path as key, and the change as value.
 *
 * Changes can be: 'create', 'update', 'delete', or 'child-update'.
 * Here, 'child-update' means the object itself is not changed but one
 * or more of it's childs have.
 *
 * @param {JSON} left
 * @param {JSON} right
 * @return {{
 *   diffLeft: DiffMap,
 *   diffRight: DiffMap
 *   changes: DiffAction[]
 * }}
 */
export function calculateDiffWithMaps (left, right) {
    const changes = calculateDiff(left, right)

    return {
        diffLeft: createDiffMapLeft(changes),
        diffRight: createDiffMapRight(changes),
        changes
    }
}

/**
 * Compare two JSON objects and return the difference between the left and
 * right object as a map with the path as key, and the change as value.
 *
 * Changes can be: 'create', 'update', 'delete'.
 *
 * @param {JSON} left
 * @param {JSON} right
 * @return {DiffAction[]} Returns a list with the changes
 */
export function calculateDiff (left, right) {
    const changes = []

    /**
     * Recursively loop over the left and right JSON object to find all differences
     * @param {JSON} left
     * @param {JSON} right
     * @param {Path} pathLeft
     * @param {Path} pathRight
     * @private
     */
    function _calculateDiff (left, right, pathLeft, pathRight) {
        // iterate over two arrays
        if (Array.isArray(left) && Array.isArray(right)) {
            arrayDiff(left, right, (change, aIndex, bIndex) => {
                const childPathLeft = pathLeft.concat([aIndex])
                const childPathRight = pathRight.concat([bIndex])

                if (change === CREATE) {
                    changes.push({ change: CREATE, pathRight: childPathRight, valueRight: right[bIndex] })
                } else if (change === UPDATE) {
                    _calculateDiff(left[aIndex], right[bIndex], childPathLeft, childPathRight)
                } else if (change === DELETE) {
                    changes.push({ change: DELETE, pathLeft: childPathLeft, valueLeft: left[aIndex] })
                }
            })

            return
        }

        // iterate over two objects
        if (isObject(left) && isObject(right)) {
            const uniqueKeys = new Set(Object.keys(left).concat(Object.keys(right)))

            uniqueKeys.forEach(key => {
                const childPathLeft = pathLeft.concat([key])
                const childPathRight = pathRight.concat([key])

                _calculateDiff(left[key], right[key], childPathLeft, childPathRight)
            })

            return
        }

        // compare any mix of primitive values or Array or Object
        if (left !== right) {
            // since we already checked whether both left and right are an Array or both are an Object,
            // we can only end up when they are not both an Array or both an Object. Hence, they
            // switched from Array to Object or vice versa
            const switchedArrayOrObjectType = Array.isArray(left) || isObject(left) || Array.isArray(right) || isObject(right)

            if (left !== undefined && right !== undefined && !switchedArrayOrObjectType) {
                changes.push({ change: UPDATE, pathLeft, pathRight, valueLeft: left, valueRight: right })
            } else {
                if (left !== undefined) {
                    changes.push({ change: DELETE, pathLeft, valueLeft: left })
                }
                if (right !== undefined) {
                    changes.push({ change: CREATE, pathRight, valueRight: right })
                }
            }
        }
    }

    _calculateDiff(left, right, [], [])

    return changes
}

/**
 * Create a diff map for the left side (having actions DELETE and UPDATE)
 * @param {DiffAction[]} changes
 * @return {DiffMap}
 */
export function createDiffMapLeft (changes) {
    const diffLeft = {}

    for (const { change, pathLeft, valueLeft } of changes) {
        if (change === DELETE || change === UPDATE) {
            const pathLeftPointer = compileJSONPointer(pathLeft)

            diffLeft[pathLeftPointer] = change

            // loop over all parent paths to mark them as having a changed child
            forEachParent(pathLeft, path => {
                const pathPointer = compileJSONPointer(path)
                if (!diffLeft[pathPointer]) {
                    diffLeft[pathPointer] = CHILD_UPDATE
                }
            })

            // loop over all children to mark them created or deleted
            if (change === DELETE && (Array.isArray(valueLeft) || isObject(valueLeft))) {
                traverse(valueLeft, pathLeft, (value, childPath) => {
                    const childPathPointer = compileJSONPointer(childPath)
                    diffLeft[childPathPointer] = change
                })
            }
        }
    }

    return diffLeft
}

/**
 * Create a diff map for the left side (having actions DELETE and UPDATE)
 * @param {DiffAction[]} changes
 * @return {DiffMap}
 */
export function createDiffMapRight (changes) {
    const diffRight = {}

    for (const { change, pathRight, valueRight } of changes) {
        if (change === CREATE || change === UPDATE) {
            const pathRightPointer = compileJSONPointer(pathRight)
            diffRight[pathRightPointer] = change

            // loop over all parent paths to mark them as having a changed child
            forEachParent(pathRight, path => {
                const pathPointer = compileJSONPointer(path)
                if (!diffRight[pathPointer]) {
                    diffRight[pathPointer] = CHILD_UPDATE
                }
            })

            // loop over all children to mark them created or deleted
            if (change === CREATE && (Array.isArray(valueRight) || isObject(valueRight))) {
                traverse(valueRight, pathRight, (value, childPath) => {
                    const childPathPointer = compileJSONPointer(childPath)
                    diffRight[childPathPointer] = change
                })
            }
        }
    }

    return diffRight
}

/**
 * Get the difference between two Arrays or strings.
 * For every change (create, update, delete) the callback function is invoked
 *
 * @param {Array<JSON> | string} a
 * @param {Array<JSON> | string} b
 * @param {function(change: 'create' | 'update' | 'delete', aIndex: number, bIndex: number)} callback
 */
export function arrayDiff (a, b, callback) {
    const diff = []
    let aIndex = 0
    let bIndex = 0

    function isCommon (aIndex, bIndex) {
        return isEqual(a[aIndex], b[bIndex])
    }

    function foundSubsequence (nCommon, aCommon, bCommon) {
        const aCount = aCommon - aIndex
        const bCount = bCommon - bIndex
        const updateCount = Math.min(aCount, bCount)

        for (let uIndex = 0; uIndex < updateCount; uIndex++) {
            callback(UPDATE, aIndex, bIndex)
            aIndex++
            bIndex++
        }

        while (aIndex < aCommon) {
            callback(DELETE, aIndex, bIndex)
            aIndex++
        }

        while (bIndex < bCommon) {
            callback(CREATE, aIndex, bIndex)
            bIndex++
        }

        aIndex += nCommon
        bIndex += nCommon
    }

    diffSequences(a.length, b.length, isCommon, foundSubsequence)
    foundSubsequence(0, a.length, b.length)

    return diff
}

/**
 * recursively loop over all items of an array or object
 * @param {JSON} json
 * @param {Path} path
 * @param {function(json: JSON, path: Path)} callback
 */
function traverse (json, path, callback) {
    callback(json, path)

    if (Array.isArray(json)) {
        for (let i = 0; i < json.length; i++) {
            traverse(json[i], path.concat([i]), callback)
        }
    } else if (isObject(json)) {
        Object.keys(json).forEach(key => {
            traverse(json[key], path.concat([key]), callback)
        })
    }
}

/**
 * Invoke a callback for every parent path of a given path like 'foo/2/bar/baz'
 * @param {Path} path
 * @param {function(parentPath: Path)} callback  Callback function
 */
export function forEachParent (path, callback) {
    for (let index = path.length - 1; index >= 0; index--) {
        const parentPath = path.slice(0, index)
        callback(parentPath)
    }
}

/**
 * Test whether a value is an object (and not null or an Array)
 * @param {JSON} json
 * @return {boolean}
 */
function isObject (json) {
    return json != null && typeof json === 'object' && !Array.isArray(json)
}
